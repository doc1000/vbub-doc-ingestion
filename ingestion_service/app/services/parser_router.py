"""Parser router — maps a canonical MIME type and extension to an extractor instance.

The orchestrator calls route_parser() once per ingestion request.
All format-to-extractor mappings live here; no branching elsewhere.
"""

from ingestion_service.app.extractors.base import DocumentExtractor
from ingestion_service.app.extractors.csv_extractor import CsvExtractor
from ingestion_service.app.extractors.docx_extractor import DocxExtractor
from ingestion_service.app.extractors.pdf_extractor import PdfExtractor
from ingestion_service.app.extractors.text_extractor import TextExtractor
from ingestion_service.app.extractors.xlsx_extractor import XlsxExtractor

_TEXT_EXTRACTOR = TextExtractor()
_PDF_EXTRACTOR = PdfExtractor()
_DOCX_EXTRACTOR = DocxExtractor()
_CSV_EXTRACTOR = CsvExtractor()
_XLSX_EXTRACTOR = XlsxExtractor()

_EXTENSION_MAP: dict[str, DocumentExtractor] = {
    "txt": _TEXT_EXTRACTOR,
    "md": _TEXT_EXTRACTOR,
    "pdf": _PDF_EXTRACTOR,
    "docx": _DOCX_EXTRACTOR,
    "csv": _CSV_EXTRACTOR,
    "xlsx": _XLSX_EXTRACTOR,
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
