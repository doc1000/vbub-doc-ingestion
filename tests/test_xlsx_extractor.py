"""Tests for XlsxExtractor."""

from pathlib import Path

import io
import openpyxl
import pytest

from vbub_doc_ingestion.extractors.xlsx_extractor import XlsxExtractor

FIXTURES = Path(__file__).parent / "fixtures"
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def extractor() -> XlsxExtractor:
    return XlsxExtractor()


@pytest.fixture
def sample_xlsx_bytes() -> bytes:
    return (FIXTURES / "sample.xlsx").read_bytes()


def test_xlsx_produces_sheet_labels(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert "## Sheet: Research Topics" in result.clean_text
    assert "## Sheet: Raw Numbers" in result.clean_text


def test_xlsx_text_rich_rows_present(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert "Machine Learning" in result.clean_text
    assert "Alice Smith" in result.clean_text
    assert "Computer Vision" in result.clean_text


def test_xlsx_numeric_only_rows_suppressed(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    # Rows like "1.0 | 2.5 | 3.7" from sheet 1 should not appear
    assert "1.0 | 2.5 | 3.7" not in result.clean_text
    assert "4.2 | 5.1 | 6.8" not in result.clean_text


def test_xlsx_header_always_retained(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert "Topic" in result.clean_text
    assert "Author" in result.clean_text


def test_xlsx_pipe_delimited_output(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert " | " in result.clean_text


def test_xlsx_title_from_first_sheet_header(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert result.title == "Topic"


def test_xlsx_parser_name_and_version(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    assert result.parser_name == "XlsxExtractor"
    assert result.parser_version == "0.1.0"


def test_xlsx_two_sheets_produce_two_blocks(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    # Two "## Sheet:" labels means two blocks
    assert result.clean_text.count("## Sheet:") == 2


def test_xlsx_numeric_only_sheet_shows_header_only(extractor: XlsxExtractor, sample_xlsx_bytes: bytes) -> None:
    """The 'Raw Numbers' sheet has all numeric body rows; only the header should remain."""
    result = extractor.extract(sample_xlsx_bytes, "sample.xlsx", _DOCX_MIME)
    # Find the Raw Numbers block
    parts = result.clean_text.split("## Sheet: Raw Numbers")
    assert len(parts) == 2
    raw_block = parts[1].strip()
    lines = [l for l in raw_block.splitlines() if l.strip()]
    # Only header row "Val1 | Val2 | Val3" should remain; no data rows
    assert len(lines) == 1
    assert "Val1" in lines[0]
