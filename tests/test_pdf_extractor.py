"""Tests for PdfExtractor."""

from pathlib import Path

import pytest

from vbub_doc_ingestion.extractors.pdf_extractor import PdfExtractor

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor() -> PdfExtractor:
    return PdfExtractor()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return (FIXTURES / "sample.pdf").read_bytes()


def test_pdf_returns_non_empty_text(extractor: PdfExtractor, sample_pdf_bytes: bytes) -> None:
    result = extractor.extract(sample_pdf_bytes, "sample.pdf", "application/pdf")
    assert result.clean_text.strip()


def test_pdf_title_from_metadata(extractor: PdfExtractor, sample_pdf_bytes: bytes) -> None:
    result = extractor.extract(sample_pdf_bytes, "sample.pdf", "application/pdf")
    assert result.title == "Quarterly Research Report"


def test_pdf_body_text_present(extractor: PdfExtractor, sample_pdf_bytes: bytes) -> None:
    result = extractor.extract(sample_pdf_bytes, "sample.pdf", "application/pdf")
    assert "Body Content" in result.clean_text
    assert "substantive body text" in result.clean_text


def test_pdf_parser_name_and_version(extractor: PdfExtractor, sample_pdf_bytes: bytes) -> None:
    result = extractor.extract(sample_pdf_bytes, "sample.pdf", "application/pdf")
    assert result.parser_name == "PdfExtractor"
    assert result.parser_version == "0.1.0"


def test_pdf_empty_page_adds_warning(extractor: PdfExtractor) -> None:
    import fitz
    doc = fitz.open()
    doc.new_page()   # page with no text
    page = doc.new_page()
    page.insert_text((72, 72), "Actual content here", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    result = extractor.extract(pdf_bytes, "empty_page.pdf", "application/pdf")
    assert any("Page 1" in w for w in result.warnings)


def test_pdf_title_falls_back_to_first_line_when_no_metadata(extractor: PdfExtractor) -> None:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Fallback Title Line\nBody paragraph here", fontsize=11)
    doc.set_metadata({"title": ""})
    pdf_bytes = doc.tobytes()
    doc.close()

    result = extractor.extract(pdf_bytes, "notitle.pdf", "application/pdf")
    assert result.title == "Fallback Title Line"
