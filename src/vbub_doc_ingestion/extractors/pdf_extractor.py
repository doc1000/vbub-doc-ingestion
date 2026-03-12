"""PDF extractor using PyMuPDF (fitz).

Extracts text from each page via page.get_text("text"), joining pages
with a double newline. Returns raw (un-normalised, un-cleaned) text;
boilerplate removal and normalisation are applied by downstream steps.

Title resolution order:
  1. Document metadata field "title" (if non-empty after stripping)
  2. First non-empty line of the extracted text
  3. None
"""

from typing import Optional

import fitz  # PyMuPDF

from vbub_doc_ingestion.domain.contracts import ExtractionResult

_PARSER_NAME = "PdfExtractor"
_PARSER_VERSION = "0.1.0"


def _resolve_title(meta_title: str, body: str) -> Optional[str]:
    """Derive a document title from metadata or body text."""
    candidate = meta_title.strip()
    if candidate:
        return candidate
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


class PdfExtractor:
    """Extracts text from PDF files using PyMuPDF.

    Implements the DocumentExtractor Protocol.
    """

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        canonical_mime: str,
    ) -> ExtractionResult:
        """Extract text from a PDF binary.

        Each page's text is separated by a double newline.
        A warning is added for any page that yields no text
        (e.g. image-only or blank pages).

        Args:
            file_bytes:     raw bytes of the PDF file.
            filename:       original filename (used for error context only).
            canonical_mime: not used for dispatch here.

        Returns:
            ExtractionResult with joined page text, optional title,
            and warnings for empty pages.
        """
        warnings: list[str] = []
        page_texts: list[str] = []

        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            meta_title: str = doc.metadata.get("title", "") or ""
            for page_number, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if not text.strip():
                    warnings.append(f"Page {page_number} yielded no text.")
                else:
                    page_texts.append(text)

        body = "\n\n".join(page_texts)
        title = _resolve_title(meta_title, body)

        return ExtractionResult(
            parser_name=_PARSER_NAME,
            parser_version=_PARSER_VERSION,
            title=title,
            clean_text=body,
            warnings=warnings,
        )
