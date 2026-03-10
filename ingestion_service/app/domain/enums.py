"""Enumerations used throughout the ingestion service.

SupportedFormat: file formats accepted by v1.
IngestionStatus: lifecycle states of a canonical document.
"""

from enum import Enum


class SupportedFormat(str, Enum):
    """File formats supported by the v1 ingestion pipeline."""

    txt = "txt"
    md = "md"
    pdf = "pdf"
    docx = "docx"
    csv = "csv"
    xlsx = "xlsx"


class IngestionStatus(str, Enum):
    """Lifecycle status values written into CanonicalDocument.

    Only values actively used in v1 are defined here.
    Do not add 'received' or 'failed' until they are needed.
    """

    processing = "processing"
    ready_for_indexing = "ready_for_indexing"
