"""Parser router — selects an extractor instance for each incoming file.

Routing policy (evaluated top-to-bottom):

1. Strong known formats route directly:
   PDF → PdfExtractor, DOCX → DocxExtractor, XLSX → XlsxExtractor, CSV → CsvExtractor.
2. If the extension is in BINARY_REJECT_EXTENSIONS, raise FileValidationError immediately.
3. If the extension is in TEXT_LIKE_EXTENSIONS, route to TextExtractor only when
   is_probably_text() confirms the content is text-like.
4. If the extension is unknown/missing but is_probably_text() returns True, route to TextExtractor.
5. Otherwise raise FileValidationError as an unsupported binary or unsupported type.

The orchestrator calls route_parser() once per ingestion request.
No format-specific branching should occur outside this module.
"""

from ingestion_service.app.extractors.base import DocumentExtractor
from ingestion_service.app.extractors.csv_extractor import CsvExtractor
from ingestion_service.app.extractors.docx_extractor import DocxExtractor
from ingestion_service.app.extractors.pdf_extractor import PdfExtractor
from ingestion_service.app.extractors.text_extractor import TextExtractor
from ingestion_service.app.extractors.xlsx_extractor import XlsxExtractor
from ingestion_service.app.services.content_classification_service import (
    BINARY_REJECT_EXTENSIONS,
    TEXT_LIKE_EXTENSIONS,
    is_probably_text,
)
from ingestion_service.app.services.file_validation_service import FileValidationError

_TEXT_EXTRACTOR = TextExtractor()
_PDF_EXTRACTOR = PdfExtractor()
_DOCX_EXTRACTOR = DocxExtractor()
_CSV_EXTRACTOR = CsvExtractor()
_XLSX_EXTRACTOR = XlsxExtractor()

# Strong-typed formats: extension unambiguously identifies both the format and
# the correct extractor.  These are checked first before any heuristic logic.
_STRONG_EXTENSION_MAP: dict[str, DocumentExtractor] = {
    "pdf": _PDF_EXTRACTOR,
    "docx": _DOCX_EXTRACTOR,
    "xlsx": _XLSX_EXTRACTOR,
    "csv": _CSV_EXTRACTOR,
}


def route_parser(
    canonical_mime: str,
    extension: str,
    file_bytes: bytes,
) -> DocumentExtractor:
    """Return the correct extractor for the given file.

    Args:
        canonical_mime: MIME type string from the validation step (informational).
        extension:      lower-case file extension without the leading dot; empty string
                        when the filename has no suffix.
        file_bytes:     raw file bytes, used for content-based heuristics.

    Returns:
        A DocumentExtractor instance appropriate for this file.

    Raises:
        FileValidationError: if the file is a known binary reject, binary content
            masquerading as text-like, or an unrecognised format that fails the
            text heuristic.
    """
    # Step 1 — route strong known formats immediately.
    if extension in _STRONG_EXTENSION_MAP:
        return _STRONG_EXTENSION_MAP[extension]

    # Step 2 — explicit binary reject list.
    if extension in BINARY_REJECT_EXTENSIONS:
        _reject_binary(extension)

    # Step 3 — text-like extension aliases (e.g. .bat, .jsx, .ps1).
    if extension in TEXT_LIKE_EXTENSIONS:
        if is_probably_text(file_bytes):
            return _TEXT_EXTRACTOR
        raise FileValidationError(
            f"File extension '.{extension}' is a text-like alias but the content "
            "appears to be binary.  The file was not routed to TextExtractor."
        )

    # Step 4 — unknown or missing extension: allow if content looks like text.
    if is_probably_text(file_bytes):
        return _TEXT_EXTRACTOR

    # Step 5 — unrecognised and binary-looking content.
    label = f".{extension}" if extension else "(no extension)"
    raise FileValidationError(
        f"Unsupported file type '{label}'.  The content does not appear to be "
        "plain text and no matching extractor was found."
    )


def _reject_binary(extension: str) -> None:
    """Raise a clear FileValidationError for explicitly rejected binary formats."""
    if extension == "xls":
        raise FileValidationError(
            "'.xls' (legacy Excel 97-2003) is not supported.  "
            "Please convert the file to '.xlsx' (Excel 2007+) and re-upload."
        )
    raise FileValidationError(
        f"'.{extension}' is a known binary format and is not supported by this service."
    )
