"""FastAPI exception handlers for the ingestion service.

All error responses share the shape:
    {"error": "<exception type name>", "detail": "<message>"}

This ensures callers never receive raw HTML tracebacks and can
always parse the error programmatically.

Handlers registered here (in order of specificity):
    FileValidationError  → 422  (validation rejection — client error)
    ValueError           → 400  (bad input that is not a file rejection)
    NotImplementedError  → 501  (pipeline step not yet implemented)
    Exception            → 500  (unexpected server error)

Registration:
    Call register_error_handlers(app) from app/main.py.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ingestion_service.app.services.file_validation_service import FileValidationError

logger = logging.getLogger(__name__)


def _error_body(exc: Exception) -> dict:
    """Build the standard error response body."""
    return {"error": type(exc).__name__, "detail": str(exc)}


def register_error_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application instance."""

    @app.exception_handler(FileValidationError)
    async def file_validation_error_handler(
        request: Request, exc: FileValidationError
    ) -> JSONResponse:
        logger.warning("File validation rejected: %s", exc)
        return JSONResponse(status_code=422, content=_error_body(exc))

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        logger.warning("Bad request (ValueError): %s", exc)
        return JSONResponse(status_code=400, content=_error_body(exc))

    @app.exception_handler(NotImplementedError)
    async def not_implemented_handler(
        request: Request, exc: NotImplementedError
    ) -> JSONResponse:
        logger.error("Not implemented: %s", exc)
        return JSONResponse(status_code=501, content=_error_body(exc))

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unexpected server error: %s", exc)
        return JSONResponse(status_code=500, content=_error_body(exc))
