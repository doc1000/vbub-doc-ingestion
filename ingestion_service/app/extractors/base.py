"""Extractor base Protocol.

All format-specific extractors implement DocumentExtractor.
The parser router returns an instance of a concrete extractor;
the orchestrator calls extract() without knowing the format.

This is the only interface contract between the router and the extractors.
Do not add format-specific logic here.
"""

from typing import Protocol

from ingestion_service.app.domain.contracts import ExtractionResult


class DocumentExtractor(Protocol):
    """Interface that every file-format extractor must satisfy."""

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        canonical_mime: str,
    ) -> ExtractionResult:
        """Extract text and metadata from raw file bytes.

        Args:
            file_bytes:     raw bytes of the uploaded file.
            filename:       original filename; used for extension hints.
            canonical_mime: MIME type detected by the validation step.

        Returns:
            An ExtractionResult containing clean_text, optional title,
            parser metadata, and any non-fatal warnings.
        """
        ...
