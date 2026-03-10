"""Integration tests for the POST /ingest/file endpoint.

Phase 3: validates that a txt/md upload returns a fully populated
CanonicalDocument with status == "readyForIndexing" and real extracted text.
"""

import hashlib
import io
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def use_tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect blob storage to a temp directory for each test."""
    monkeypatch.setenv("BINARY_STORAGE_PATH", str(tmp_path))
    # Also patch the module-level constant that was already read at import time.
    import ingestion_service.app.orchestration.ingest_file as orch
    monkeypatch.setattr(orch, "_STORAGE_ROOT", str(tmp_path))


def _post_file(
    client: TestClient,
    content: bytes,
    filename: str,
    tags: list[str] | None = None,
) -> dict:
    meta: dict = {"original_filename": filename}
    if tags is not None:
        meta["user_tags"] = tags
    response = client.post(
        "/ingest/file",
        files={"file": (filename, io.BytesIO(content), "text/plain")},
        data={"client_meta": json.dumps(meta)},
    )
    return response


def test_upload_txt_returns_200(client: TestClient) -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample.txt"
    content = fixture.read_bytes()
    response = _post_file(client, content, "sample.txt")
    assert response.status_code == 200


def test_response_contains_binary_ref_with_correct_sha256(client: TestClient) -> None:
    content = b"deterministic content for hashing"
    expected_sha256 = hashlib.sha256(content).hexdigest()
    response = _post_file(client, content, "check.txt")
    assert response.status_code == 200
    payload = response.json()
    assert payload["binaryRef"]["checksumSha256"] == expected_sha256
    assert payload["binaryRef"]["sizeBytes"] == len(content)


def test_response_contains_validated_tags(client: TestClient) -> None:
    content = b"tagged content"
    response = _post_file(client, content, "tagged.txt", tags=["Research", "  Finance  "])
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["tags"] == ["research", "finance"]


def test_status_is_ready_for_indexing(client: TestClient) -> None:
    response = _post_file(client, b"hello world", "hello.txt")
    assert response.status_code == 200
    # The IngestionStatus enum value serialises as the raw string "ready_for_indexing".
    assert response.json()["status"] == "ready_for_indexing"


def test_txt_extraction_contains_real_text(client: TestClient) -> None:
    content = b"Ingestion test content line one\nLine two here"
    response = _post_file(client, content, "real.txt")
    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction"]["parserName"] == "TextExtractor"
    assert "Ingestion test content" in payload["extraction"]["cleanText"]


def test_txt_extraction_sets_title(client: TestClient) -> None:
    content = b"Document Title\nBody text here"
    response = _post_file(client, content, "titled.txt")
    payload = response.json()
    assert payload["extraction"]["title"] == "Document Title"


def test_md_upload_strips_front_matter(client: TestClient) -> None:
    from pathlib import Path
    fixture = Path(__file__).parent / "fixtures" / "sample.md"
    content = fixture.read_bytes()
    response = _post_file(client, content, "sample.md")
    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction"]["title"] == "Sample Heading"
    assert "title:" not in payload["extraction"]["cleanText"]
    assert "---" not in payload["extraction"]["cleanText"]


def test_document_id_has_doc_prefix(client: TestClient) -> None:
    response = _post_file(client, b"id check", "id.txt")
    assert response.json()["documentId"].startswith("doc_")


def test_unsupported_extension_returns_422(client: TestClient) -> None:
    response = _post_file(client, b"data", "archive.zip")
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_malformed_client_meta_returns_400(client: TestClient) -> None:
    response = client.post(
        "/ingest/file",
        files={"file": ("f.txt", io.BytesIO(b"x"), "text/plain")},
        data={"client_meta": "not-valid-json"},
    )
    assert response.status_code == 400


def test_binary_file_written_to_storage(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"binary preservation check"
    response = _post_file(client, content, "preserve.txt")
    assert response.status_code == 200
    storage_key = response.json()["binaryRef"]["storageKey"]
    stored = (tmp_path / storage_key).read_bytes()
    assert stored == content
