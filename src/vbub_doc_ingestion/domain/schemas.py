"""Domain request schemas for the ingestion pipeline.

ClientMeta: structured representation of the metadata submitted
alongside every file upload or direct orchestration call.

Rules:
- ClientMeta is a pure-domain model — no FastAPI dependency.
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
