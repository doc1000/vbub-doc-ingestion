"""FastAPI application entry point for the ingestion service.

Registers:
- GET /health  — liveness check
- POST /ingest/file — document upload endpoint (via routes_ingest router)
"""

from fastapi import FastAPI

from ingestion_service.app.api.routes_ingest import router as ingest_router

app = FastAPI(title="vbub-doc-ingestion", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 when the service is running."""
    return {"status": "ok"}


app.include_router(ingest_router)
