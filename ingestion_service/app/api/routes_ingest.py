"""Ingest API routes.

Exposes POST /ingest/file — the single upload endpoint.

This module is transport only:
- Parse the multipart request.
- Parse client_meta JSON into ClientMeta.
- Delegate entirely to orchestrate_ingestion().
- Return the result.

No business logic belongs here.
"""

import json

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import ValidationError

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.domain.contracts import CanonicalDocument
from ingestion_service.app.orchestration.ingest_file import orchestrate_ingestion
from ingestion_service.app.services.file_validation_service import FileValidationError

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
        raise HTTPException(status_code=400, detail=f"Invalid client_meta: {exc}") from exc

    file_bytes = await file.read()
    filename = meta.original_filename or (file.filename or "unknown")

    try:
        return orchestrate_ingestion(
            file_bytes=file_bytes,
            filename=filename,
            client_meta=meta,
        )
    except FileValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
