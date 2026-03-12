"""vbub_doc_ingestion — reusable document-ingestion pipeline.

Import mode:
    from vbub_doc_ingestion import orchestrate_ingestion, ClientMeta
    doc = orchestrate_ingestion(file_bytes, filename, client_meta)

Service mode:
    uvicorn adapters.fastapi_app.main:app
"""

__version__ = "0.1.0"

from vbub_doc_ingestion.domain.contracts import CanonicalDocument
from vbub_doc_ingestion.domain.schemas import ClientMeta
from vbub_doc_ingestion.orchestration.ingest_file import orchestrate_ingestion

__all__ = ["__version__", "orchestrate_ingestion", "CanonicalDocument", "ClientMeta"]
