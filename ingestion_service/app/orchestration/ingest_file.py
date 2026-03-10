"""Ingestion orchestration — ingest_file pipeline.

orchestrate_ingestion() is the single entry point for the ingestion
pipeline. It coordinates all service calls in order and returns a
CanonicalDocument.

Pipeline steps:
  1. validate_file        — check size, MIME, extension, compute SHA-256
  2. validate_tags        — normalise and validate user-supplied tags
  3. store binary         — write original bytes to blob store, build BinaryRef
  4. route_parser         — select the correct extractor for the file type
  5. extract              — run the extractor, get raw text + parser metadata
  6. normalize_text       — Unicode, whitespace, encoding cleanup
  [Phase 4 TODO: remove_boilerplate — strip repeated headers/footers (PDF only)]
  7. assemble             — build and return the CanonicalDocument

Rules:
- This function must stay thin. No format-specific logic belongs here.
- Call one function per step; keep branching out of this file.
- Do not import FastAPI objects into this module.
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.domain.contracts import (
    BinaryRef,
    CanonicalDocument,
    SourceLocator,
)
from ingestion_service.app.domain.enums import IngestionStatus
from ingestion_service.app.services.file_validation_service import validate_file
from ingestion_service.app.services.parser_router import route_parser
from ingestion_service.app.services.tag_policy_service import validate_tags
from ingestion_service.app.services.text_normalization_service import normalize_text
from ingestion_service.app.storage.blob_store import LocalBlobStore

_STORAGE_ROOT = os.environ.get("BINARY_STORAGE_PATH", "./data/blobs")


def orchestrate_ingestion(
    file_bytes: bytes,
    filename: str,
    client_meta: ClientMeta,
) -> CanonicalDocument:
    """Run the full ingestion pipeline and return a CanonicalDocument.

    Args:
        file_bytes:  raw bytes of the uploaded file.
        filename:    display filename (from client_meta.original_filename).
        client_meta: validated metadata submitted by the client.

    Returns:
        A fully populated CanonicalDocument with status = ready_for_indexing.
    """
    # Step 1 — validate file (raises FileValidationError on rejection)
    validation = validate_file(file_bytes, filename, client_meta)

    # Step 2 — validate and normalise user tags
    tags = validate_tags(client_meta.user_tags)

    # Step 3 — store original binary; build BinaryRef inline
    store = LocalBlobStore(_STORAGE_ROOT)
    storage_key = store.put(file_bytes, filename, validation.sha256)
    binary_ref = BinaryRef(
        storage_key=storage_key,
        checksum_sha256=validation.sha256,
        size_bytes=validation.size_bytes,
    )

    source_locator = SourceLocator(
        device_label=client_meta.device_label,
        os_label=client_meta.os_label,
        local_path_hint=client_meta.local_path_hint,
    )

    # Step 4 — select extractor (raises ValueError for unsupported formats)
    extractor = route_parser(validation.canonical_mime, validation.extension)

    # Step 5 — extract raw text and parser metadata
    extraction = extractor.extract(file_bytes, filename, validation.canonical_mime)

    # Step 6 — normalise text (encoding, line endings, whitespace, smart quotes)
    # TODO Phase 4: run remove_boilerplate(extraction.clean_text, validation.canonical_mime) here for PDF
    extraction = extraction.model_copy(
        update={"clean_text": normalize_text(extraction.clean_text)}
    )

    # Step 7 — assemble canonical document
    return CanonicalDocument.assemble(
        document_id="doc_" + uuid4().hex[:12],
        display_name=filename,
        canonical_mime=validation.canonical_mime,
        extension=validation.extension,
        binary_ref=binary_ref,
        source_locator=source_locator,
        extraction=extraction,
        tags=tags,
        status=IngestionStatus.ready_for_indexing,
        created_at=datetime.now(timezone.utc),
    )
