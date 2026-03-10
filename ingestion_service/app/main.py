"""FastAPI application entry point for the ingestion service.

Registers:
- GET /health  — liveness check
- POST /ingest/file — document upload endpoint (via routes_ingest router)
- Exception handlers — structured JSON error responses (via error_handlers)

Startup log emits the service name and environment so deployments are
easy to identify in log aggregators.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from ingestion_service.app.api.error_handlers import register_error_handlers
from ingestion_service.app.api.routes_ingest import router as ingest_router
from ingestion_service.app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s | env=%s | log_level=%s | max_upload_mb=%s | storage=%s",
        settings.service_name,
        settings.app_env,
        settings.log_level,
        settings.max_upload_size_mb,
        settings.binary_storage_path,
    )
    yield


app = FastAPI(title=settings.service_name, version="0.1.0", lifespan=_lifespan)

register_error_handlers(app)


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 when the service is running."""
    return {"status": "ok"}


app.include_router(ingest_router)
