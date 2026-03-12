"""Verify the public package API is importable and functional without FastAPI."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def use_tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect blob storage to a temp directory for each test."""
    import vbub_doc_ingestion.config as cfg
    monkeypatch.setattr(cfg.settings, "binary_storage_path", str(tmp_path))


def test_public_imports() -> None:
    from vbub_doc_ingestion import CanonicalDocument, ClientMeta, orchestrate_ingestion
    assert callable(orchestrate_ingestion)
    assert CanonicalDocument is not None
    assert ClientMeta is not None


def test_orchestrate_ingestion_returns_canonical_document() -> None:
    from vbub_doc_ingestion import CanonicalDocument, ClientMeta, orchestrate_ingestion

    meta = ClientMeta(original_filename="hello.txt")
    doc = orchestrate_ingestion(
        file_bytes=b"Hello from package API test",
        filename="hello.txt",
        client_meta=meta,
    )
    assert isinstance(doc, CanonicalDocument)
    assert doc.status.value == "ready_for_indexing"
    assert doc.document_id.startswith("doc_")
    assert "Hello from package API test" in doc.extraction.clean_text


def test_canonical_document_round_trips_to_json() -> None:
    from vbub_doc_ingestion import ClientMeta, orchestrate_ingestion

    meta = ClientMeta(original_filename="round.txt")
    doc = orchestrate_ingestion(
        file_bytes=b"Round-trip test content",
        filename="round.txt",
        client_meta=meta,
    )
    data = doc.model_dump(by_alias=True)
    assert "documentId" in data
    assert "binaryRef" in data
    assert "extraction" in data
