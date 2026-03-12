"""Tests for the health endpoint, the Phase 1 ingest stub, and contract serialisation."""

import io
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from vbub_doc_ingestion.domain.contracts import (
    BinaryRef,
    CanonicalDocument,
    ExtractionResult,
    SourceLocator,
)
from vbub_doc_ingestion.domain.enums import IngestionStatus


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_file_stub_returns_501(client: TestClient) -> None:
    """Phase 1 stub test — retained but updated.

    The endpoint now executes real Phase 2 logic (validation + storage).
    A .txt file returns 200. This test is superseded by test_ingest_file.py
    but kept here as a record of the Phase 1 → Phase 2 transition.
    The 501 path is still reachable for any future NotImplementedError;
    it is tested in test_ingest_file.py via unsupported formats.
    """
    client_meta = json.dumps({"original_filename": "test.txt"})
    response = client.post(
        "/ingest/file",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"client_meta": client_meta},
    )
    # Phase 2: real pipeline runs, returns 200 for a supported format.
    assert response.status_code == 200


def test_canonical_document_serialises_to_camel_case() -> None:
    """CanonicalDocument.assemble() must produce camelCase JSON matching the README example.

    Field mapping verified (snake_case Python -> camelCase JSON):
        document_id       -> documentId
        display_name      -> displayName
        canonical_mime    -> canonicalMime
        binary_ref        -> binaryRef
          storage_key     ->   storageKey
          checksum_sha256 ->   checksumSha256
          size_bytes      ->   sizeBytes
        source_locator    -> sourceLocator
          device_label    ->   deviceLabel
          os_label        ->   osLabel
          local_path_hint ->   localPathHint
        extraction
          parser_name     ->   parserName
          parser_version  ->   parserVersion
          clean_text      ->   cleanText
        metadata
          created_at      ->   createdAt
        status            -> status  (enum value, no rename)
    """
    doc = CanonicalDocument.assemble(
        document_id="doc_123",
        display_name="report.docx",
        canonical_mime=(
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        ),
        extension="docx",
        binary_ref=BinaryRef(
            storage_key="blob/abc123",
            checksum_sha256="abc...",
            size_bytes=182334,
        ),
        source_locator=SourceLocator(
            device_label="PersonalLaptop",
            os_label="Windows 11",
            local_path_hint="C:/documents/report.docx",
        ),
        extraction=ExtractionResult(
            parser_name="DocxExtractor",
            parser_version="0.1.0",
            title="Quarterly Report",
            clean_text="normalized document text...",
            warnings=[],
        ),
        tags=["research", "finance"],
        status=IngestionStatus.ready_for_indexing,
        created_at=datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    payload = json.loads(doc.model_dump_json(by_alias=True))

    # Top-level camelCase keys
    assert payload["documentId"] == "doc_123"
    assert payload["displayName"] == "report.docx"
    assert "canonicalMime" in payload
    assert payload["extension"] == "docx"
    assert payload["status"] == "ready_for_indexing"

    # binaryRef nested keys
    binary_ref = payload["binaryRef"]
    assert binary_ref["storageKey"] == "blob/abc123"
    assert binary_ref["checksumSha256"] == "abc..."
    assert binary_ref["sizeBytes"] == 182334

    # sourceLocator nested keys
    source = payload["sourceLocator"]
    assert source["deviceLabel"] == "PersonalLaptop"
    assert source["osLabel"] == "Windows 11"
    assert source["localPathHint"] == "C:/documents/report.docx"

    # extraction nested keys
    extraction = payload["extraction"]
    assert extraction["parserName"] == "DocxExtractor"
    assert extraction["parserVersion"] == "0.1.0"
    assert extraction["title"] == "Quarterly Report"
    assert extraction["cleanText"] == "normalized document text..."
    assert extraction["warnings"] == []

    # metadata nested keys
    metadata = payload["metadata"]
    assert metadata["tags"] == ["research", "finance"]
    assert "createdAt" in metadata

    # Confirm no snake_case keys leaked into the output
    all_keys = (
        list(payload)
        + list(binary_ref)
        + list(source)
        + list(extraction)
        + list(metadata)
    )
    snake_case_keys = [k for k in all_keys if "_" in k]
    assert snake_case_keys == [], f"Snake-case keys found in JSON output: {snake_case_keys}"

