"""Ingest API routes.

Exposes POST /ingest/file — the single upload endpoint.

This module is transport only:
- Parse the multipart request.
- Parse client_meta JSON into ClientMeta.
- Delegate entirely to orchestrate_ingestion().
- Return the result.

No business logic belongs here. Error responses are handled by the
exception handlers registered in error_handlers.py; explicit try/except
is only used here for the client_meta parse step, where we need to
surface a clean 400 before the request even reaches the orchestrator.
"""

import json
import logging

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import ValidationError

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.domain.contracts import CanonicalDocument
from ingestion_service.app.orchestration.ingest_file import orchestrate_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest")


@router.post("/file", response_model=CanonicalDocument)
async def ingest_file(
    file: UploadFile,
    client_meta: str = Form(...),
) -> CanonicalDocument:
    """Accept a single file upload and return a CanonicalDocument.

    Multipart fields:
        file:        the binary file to ingest.
        client_meta: JSON string conforming to the ClientMeta schema.
    """
    try:
        meta = ClientMeta.model_validate(json.loads(client_meta))
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("Bad client_meta: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid client_meta: {exc}") from exc

    file_bytes = await file.read()
    filename = meta.original_filename or (file.filename or "unknown")
    logger.info("Request received | filename=%s | size_bytes=%d", filename, len(file_bytes))

    result = orchestrate_ingestion(
        file_bytes=file_bytes,
        filename=filename,
        client_meta=meta,
    )

    logger.info(
        "Response sent | document_id=%s | filename=%s | status=%s",
        result.document_id,
        filename,
        result.status,
    )
    return result
