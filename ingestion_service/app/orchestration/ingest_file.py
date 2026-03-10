"""Ingestion orchestration — ingest_file pipeline.

orchestrate_ingestion() is the single entry point for the ingestion
pipeline. It coordinates all service calls in order and returns a
CanonicalDocument.

Pipeline steps (to be implemented in later phases):
  1. validate_file        — check size, MIME, extension, compute SHA-256
  2. validate_tags        — normalise and validate user-supplied tags
  3. store binary         — write original bytes to blob store, build BinaryRef
  4. route_parser         — select the correct extractor for the file type
  5. extract              — run the extractor, get raw text + parser metadata
  6. remove_boilerplate   — strip repeated headers/footers (PDF; Phase 4)
  7. normalize_text       — Unicode, whitespace, encoding cleanup
  8. assemble             — build and return the CanonicalDocument

Rules:
- This function must stay thin. No format-specific logic belongs here.
- Call one function per step; keep branching out of this file.
- Do not import FastAPI objects into this module.
"""

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.domain.contracts import CanonicalDocument


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
        A fully populated CanonicalDocument.

    Raises:
        NotImplementedError: pipeline steps are not yet implemented (Phase 1 stub).
    """
    # TODO Phase 2: validate_file(file_bytes, filename, client_meta)
    # TODO Phase 2: validate_tags(client_meta.user_tags)
    # TODO Phase 2: LocalBlobStore.put(...) -> storage_key; build BinaryRef inline
    # TODO Phase 3: route_parser(canonical_mime, extension) -> extractor
    # TODO Phase 3: extractor.extract(file_bytes, filename, canonical_mime)
    # TODO Phase 4: remove_boilerplate(raw_text, canonical_mime)
    # TODO Phase 3: normalize_text(raw_text)
    # TODO Phase 3: CanonicalDocument.assemble(...)

    raise NotImplementedError("Ingestion pipeline not yet implemented.")
