"""API-layer request schemas for the ingestion service.

ClientMeta: structured representation of the JSON metadata string
submitted alongside every file upload.

Rules:
- Do NOT add IngestFileRequest or IngestFileResponse wrappers.
- FastAPI route signatures define the multipart contract directly.
- ClientMeta is the only schema needed here in Phase 1.
"""

from typing import Optional

from pydantic import BaseModel


class ClientMeta(BaseModel):
    """Metadata submitted by the client alongside the uploaded file.

    All fields except original_filename are optional; clients may
    omit any they cannot provide.
    """

    original_filename: str
    browser_mime: Optional[str] = None
    size_bytes: Optional[int] = None
    local_path_hint: Optional[str] = None
    device_label: Optional[str] = None
    os_label: Optional[str] = None
    user_tags: Optional[list[str]] = None
