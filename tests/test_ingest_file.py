"""Integration tests for the POST /ingest/file endpoint.

Phase 5: adds CSV and XLSX upload tests. Confirms all six v1 formats
return the same payload shape.
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


# ---------------------------------------------------------------------------
# Phase 4: PDF and DOCX integration tests
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


def test_pdf_upload_returns_200(client: TestClient) -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = _post_file(client, content, "sample.pdf")
    assert response.status_code == 200


def test_pdf_status_is_ready_for_indexing(client: TestClient) -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = _post_file(client, content, "sample.pdf")
    assert response.json()["status"] == "ready_for_indexing"


def test_pdf_clean_text_is_non_empty(client: TestClient) -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = _post_file(client, content, "sample.pdf")
    payload = response.json()
    assert payload["extraction"]["cleanText"].strip()
    assert payload["extraction"]["parserName"] == "PdfExtractor"


def test_pdf_repeated_header_footer_removed(client: TestClient) -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = _post_file(client, content, "sample.pdf")
    clean_text = response.json()["extraction"]["cleanText"]
    # The fixture has "Acme Corp Confidential" and "Internal Use Only" repeated
    # on all 3 pages — boilerplate cleanup should remove them.
    assert "Acme Corp Confidential" not in clean_text
    assert "Internal Use Only" not in clean_text


def test_docx_upload_returns_200(client: TestClient) -> None:
    content = (FIXTURES / "sample.docx").read_bytes()
    response = _post_file(client, content, "sample.docx")
    assert response.status_code == 200


def test_docx_status_is_ready_for_indexing(client: TestClient) -> None:
    content = (FIXTURES / "sample.docx").read_bytes()
    response = _post_file(client, content, "sample.docx")
    assert response.json()["status"] == "ready_for_indexing"


def test_docx_clean_text_is_non_empty(client: TestClient) -> None:
    content = (FIXTURES / "sample.docx").read_bytes()
    response = _post_file(client, content, "sample.docx")
    payload = response.json()
    assert payload["extraction"]["cleanText"].strip()
    assert payload["extraction"]["parserName"] == "DocxExtractor"


def test_payload_shape_consistent_across_formats(client: TestClient) -> None:
    """Top-level JSON keys must be identical for txt, pdf, docx, csv, and xlsx responses."""
    EXPECTED_TOP_KEYS = {
        "documentId", "displayName", "canonicalMime", "extension",
        "binaryRef", "sourceLocator", "extraction", "metadata", "status",
    }
    for filename, content_path in [
        ("sample.txt", FIXTURES / "sample.txt"),
        ("sample.pdf", FIXTURES / "sample.pdf"),
        ("sample.docx", FIXTURES / "sample.docx"),
        ("sample.csv", FIXTURES / "sample.csv"),
        ("sample.xlsx", FIXTURES / "sample.xlsx"),
    ]:
        content = content_path.read_bytes()
        response = _post_file(client, content, filename)
        assert response.status_code == 200, f"Failed for {filename}: {response.text}"
        assert set(response.json().keys()) == EXPECTED_TOP_KEYS, (
            f"Key mismatch for {filename}: {set(response.json().keys())}"
        )


# ---------------------------------------------------------------------------
# Phase 5: CSV and XLSX integration tests
# ---------------------------------------------------------------------------


def test_csv_upload_returns_200(client: TestClient) -> None:
    content = (FIXTURES / "sample.csv").read_bytes()
    response = _post_file(client, content, "sample.csv")
    assert response.status_code == 200


def test_csv_status_is_ready_for_indexing(client: TestClient) -> None:
    content = (FIXTURES / "sample.csv").read_bytes()
    response = _post_file(client, content, "sample.csv")
    assert response.json()["status"] == "ready_for_indexing"


def test_csv_clean_text_is_pipe_delimited(client: TestClient) -> None:
    content = (FIXTURES / "sample.csv").read_bytes()
    response = _post_file(client, content, "sample.csv")
    payload = response.json()
    assert " | " in payload["extraction"]["cleanText"]
    assert payload["extraction"]["parserName"] == "CsvExtractor"


def test_csv_numeric_rows_absent_from_response(client: TestClient) -> None:
    content = (FIXTURES / "sample.csv").read_bytes()
    response = _post_file(client, content, "sample.csv")
    clean_text = response.json()["extraction"]["cleanText"]
    # The fixture rows "1.0,2.5,3.7" and "4.2,5.1,6.8" should be suppressed
    assert "1.0" not in clean_text or "Machine Learning" in clean_text  # header kept
    lines = clean_text.splitlines()
    for line in lines:
        cells = [c.strip() for c in line.split("|")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue
        all_numeric = all(_try_float(c) for c in non_empty)
        assert not all_numeric, f"Numeric-only row found in response: {line}"


def _try_float(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False


def test_xlsx_upload_returns_200(client: TestClient) -> None:
    content = (FIXTURES / "sample.xlsx").read_bytes()
    response = _post_file(client, content, "sample.xlsx")
    assert response.status_code == 200


def test_xlsx_status_is_ready_for_indexing(client: TestClient) -> None:
    content = (FIXTURES / "sample.xlsx").read_bytes()
    response = _post_file(client, content, "sample.xlsx")
    assert response.json()["status"] == "ready_for_indexing"


def test_xlsx_clean_text_has_sheet_labels(client: TestClient) -> None:
    content = (FIXTURES / "sample.xlsx").read_bytes()
    response = _post_file(client, content, "sample.xlsx")
    payload = response.json()
    assert "## Sheet:" in payload["extraction"]["cleanText"]
    assert payload["extraction"]["parserName"] == "XlsxExtractor"


def test_xlsx_text_rows_present_numeric_suppressed(client: TestClient) -> None:
    content = (FIXTURES / "sample.xlsx").read_bytes()
    response = _post_file(client, content, "sample.xlsx")
    clean_text = response.json()["extraction"]["cleanText"]
    assert "Machine Learning" in clean_text
    assert "1.0 | 2.5 | 3.7" not in clean_text
