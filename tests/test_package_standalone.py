"""Standalone integration test — proves the package works without FastAPI.

This test must NOT import FastAPI or use TestClient.
It validates the primary usage mode: importing the package directly.
"""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def use_tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import vbub_doc_ingestion.config as cfg
    monkeypatch.setattr(cfg.settings, "binary_storage_path", str(tmp_path))


def test_txt_ingestion_standalone() -> None:
    from vbub_doc_ingestion import CanonicalDocument, ClientMeta, orchestrate_ingestion

    meta = ClientMeta(original_filename="standalone.txt")
    doc = orchestrate_ingestion(
        file_bytes=b"Standalone ingestion test content",
        filename="standalone.txt",
        client_meta=meta,
    )

    assert isinstance(doc, CanonicalDocument)
    assert doc.status.value == "ready_for_indexing"
    assert doc.document_id.startswith("doc_")
    assert doc.display_name == "standalone.txt"
    assert doc.extension == "txt"
    assert "Standalone ingestion test" in doc.extraction.clean_text
    assert doc.extraction.parser_name == "TextExtractor"


def test_json_round_trip_standalone() -> None:
    from vbub_doc_ingestion import ClientMeta, orchestrate_ingestion

    meta = ClientMeta(
        original_filename="round.txt",
        user_tags=["test", "standalone"],
    )
    doc = orchestrate_ingestion(
        file_bytes=b"JSON round-trip verification content",
        filename="round.txt",
        client_meta=meta,
    )

    data = doc.model_dump(by_alias=True)

    assert "documentId" in data
    assert "binaryRef" in data
    assert "extraction" in data
    assert data["metadata"]["tags"] == ["test", "standalone"]
    assert data["status"] == "ready_for_indexing"


def test_version_accessible() -> None:
    from vbub_doc_ingestion import __version__
    assert __version__ == "0.1.0"
