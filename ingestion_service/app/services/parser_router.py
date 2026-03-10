"""Parser router — maps a canonical MIME type and extension to an extractor instance.

The orchestrator calls route_parser() once per ingestion request.
All format-to-extractor mappings live here; no branching elsewhere.

Only txt and md are supported in Phase 3.
Additional extractors are registered here in later phases.
"""

from ingestion_service.app.extractors.base import DocumentExtractor
from ingestion_service.app.extractors.text_extractor import TextExtractor

_TEXT_EXTRACTOR = TextExtractor()

_EXTENSION_MAP: dict[str, DocumentExtractor] = {
    "txt": _TEXT_EXTRACTOR,
    "md": _TEXT_EXTRACTOR,
}


def route_parser(canonical_mime: str, extension: str) -> DocumentExtractor:
    """Return the correct extractor for the given file type.

    Args:
        canonical_mime: MIME type string from the validation step (informational).
        extension:      lower-case file extension without the leading dot.

    Returns:
        A DocumentExtractor instance for the given format.

    Raises:
        ValueError: if the extension has no registered extractor.
    """
    extractor = _EXTENSION_MAP.get(extension)
    if extractor is None:
        raise ValueError(f"unsupported format: {extension}")
    return extractor
