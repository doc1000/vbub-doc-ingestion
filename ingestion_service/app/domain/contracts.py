"""Domain contracts for the ingestion service.

These are the canonical Pydantic models shared across all layers.
They define the public shape of the CanonicalDocument payload returned
to downstream consumers.

Rules:
- Field names are snake_case in Python.
- JSON output uses camelCase via alias_generator.
- Do NOT modify CanonicalDocument shape without an explicit plan change.
- Do NOT add CleanTextResult, IngestFileRequest, or IngestFileResponse here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ingestion_service.app.domain.enums import IngestionStatus


class _CamelModel(BaseModel):
    """Base model that serialises to camelCase JSON and accepts both forms on input."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class BinaryRef(_CamelModel):
    """Reference to the stored original binary file.

    storage_key:     relative path under the configured storage root.
    checksum_sha256: hex-encoded SHA-256 digest of the original bytes.
    size_bytes:      byte length of the stored file.
    """

    storage_key: str
    checksum_sha256: str
    size_bytes: int


class SourceLocator(_CamelModel):
    """Human-readable hints about where the file originated.

    All fields are optional — the user may supply none, some, or all.
    These are informational only; the service does not validate or
    dereference the local path.
    """

    device_label: Optional[str] = None
    os_label: Optional[str] = None
    local_path_hint: Optional[str] = None


class ExtractionResult(_CamelModel):
    """Output produced by a parser extractor.

    parser_name:    class name of the extractor that produced this result.
    parser_version: semver string of the extractor.
    title:          document title if detected; None otherwise.
    clean_text:     normalised, human-readable text of the document.
    warnings:       non-fatal issues encountered during extraction.
    """

    parser_name: str
    parser_version: str
    title: Optional[str] = None
    clean_text: str
    warnings: list[str] = []


class DocumentMetadata(_CamelModel):
    """User-supplied and ingestion-time metadata.

    tags:       validated, normalised list of user tags.
    created_at: UTC timestamp at which the ingestion request was received.
    """

    tags: list[str] = []
    created_at: datetime


class CanonicalDocument(_CamelModel):
    """The single ingestion contract returned to all downstream consumers.

    This is the only payload shape downstream systems should ever read.
    Parse once here; never branch on file type downstream.
    """

    document_id: str
    display_name: str
    canonical_mime: str
    extension: str
    binary_ref: BinaryRef
    source_locator: SourceLocator
    extraction: ExtractionResult
    metadata: DocumentMetadata
    status: IngestionStatus

    @classmethod
    def assemble(
        cls,
        *,
        document_id: str,
        display_name: str,
        canonical_mime: str,
        extension: str,
        binary_ref: BinaryRef,
        source_locator: SourceLocator,
        extraction: ExtractionResult,
        tags: list[str],
        status: IngestionStatus,
        created_at: Optional[datetime] = None,
    ) -> "CanonicalDocument":
        """Construct a CanonicalDocument from the outputs of prior pipeline steps.

        created_at defaults to the current UTC time when not supplied.
        This is the single assembly point — do not construct CanonicalDocument
        directly elsewhere in the pipeline.
        """
        return cls(
            document_id=document_id,
            display_name=display_name,
            canonical_mime=canonical_mime,
            extension=extension,
            binary_ref=binary_ref,
            source_locator=source_locator,
            extraction=extraction,
            metadata=DocumentMetadata(
                tags=tags,
                created_at=created_at or datetime.now(timezone.utc),
            ),
            status=status,
        )
