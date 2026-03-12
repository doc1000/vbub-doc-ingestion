"""Tests for CsvExtractor."""

from pathlib import Path

import pytest

from vbub_doc_ingestion.extractors.csv_extractor import CsvExtractor

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor() -> CsvExtractor:
    return CsvExtractor()


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return (FIXTURES / "sample.csv").read_bytes()


def test_csv_returns_pipe_delimited_text(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert " | " in result.clean_text


def test_csv_header_row_always_present(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert "Topic" in result.clean_text
    assert "Author" in result.clean_text
    assert "Summary" in result.clean_text


def test_csv_text_rich_rows_present(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert "Machine Learning" in result.clean_text
    assert "Alice Smith" in result.clean_text
    assert "Computer Vision" in result.clean_text


def test_csv_numeric_only_rows_suppressed(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    lines = result.clean_text.splitlines()
    for line in lines:
        cells = [c.strip() for c in line.split("|")]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue
        try:
            numeric_count = sum(1 for c in non_empty if float(c.replace(",", "")) or True)
        except ValueError:
            continue
        # If all cells are numeric, this row should not be present
        all_numeric = all(_is_numeric(c) for c in non_empty)
        assert not all_numeric, f"Numeric-only row leaked into output: {line}"


def _is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False


def test_csv_parser_name_and_version(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert result.parser_name == "CsvExtractor"
    assert result.parser_version == "0.1.0"


def test_csv_title_from_first_header_cell(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert result.title == "Topic"


def test_csv_utf8_bom_handled(extractor: CsvExtractor) -> None:
    csv_with_bom = "Name,Value\nAlpha,Beta\n".encode("utf-8-sig")
    result = extractor.extract(csv_with_bom, "bom.csv", "text/csv")
    assert "Name" in result.clean_text
    assert "\ufeff" not in result.clean_text


def test_csv_warnings_empty(extractor: CsvExtractor, sample_csv_bytes: bytes) -> None:
    result = extractor.extract(sample_csv_bytes, "sample.csv", "text/csv")
    assert result.warnings == []
