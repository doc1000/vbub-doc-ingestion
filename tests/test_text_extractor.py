"""Tests for TextExtractor (txt and md files)."""

from pathlib import Path

import pytest

from ingestion_service.app.extractors.text_extractor import TextExtractor

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor() -> TextExtractor:
    return TextExtractor()


def test_txt_returns_content(extractor: TextExtractor) -> None:
    result = extractor.extract(b"Hello world\nSecond line", "doc.txt", "text/plain")
    assert "Hello world" in result.clean_text
    assert result.parser_name == "TextExtractor"
    assert result.parser_version == "0.1.0"


def test_txt_extracts_first_line_as_title(extractor: TextExtractor) -> None:
    result = extractor.extract(b"My Title\nBody text here", "doc.txt", "text/plain")
    assert result.title == "My Title"


def test_txt_title_skips_empty_leading_lines(extractor: TextExtractor) -> None:
    result = extractor.extract(b"\n\n  \nActual Title\nBody", "doc.txt", "text/plain")
    assert result.title == "Actual Title"


def test_utf8_bom_is_stripped(extractor: TextExtractor) -> None:
    # encode("utf-8-sig") prepends the BOM byte sequence; decode should strip it.
    content_with_bom = "Hello BOM".encode("utf-8-sig")
    result = extractor.extract(content_with_bom, "bom.txt", "text/plain")
    assert result.clean_text.startswith("Hello BOM")
    assert "\ufeff" not in result.clean_text


def test_latin1_fallback(extractor: TextExtractor) -> None:
    latin1_bytes = "caf\xe9".encode("latin-1")
    result = extractor.extract(latin1_bytes, "file.txt", "text/plain")
    assert "caf" in result.clean_text


def test_md_strips_yaml_front_matter(extractor: TextExtractor) -> None:
    fixture = FIXTURES / "sample.md"
    result = extractor.extract(fixture.read_bytes(), "sample.md", "text/markdown")
    assert "title:" not in result.clean_text
    assert "author:" not in result.clean_text
    assert "---" not in result.clean_text


def test_md_extracts_h1_as_title(extractor: TextExtractor) -> None:
    fixture = FIXTURES / "sample.md"
    result = extractor.extract(fixture.read_bytes(), "sample.md", "text/markdown")
    assert result.title == "Sample Heading"


def test_md_preserves_body_text(extractor: TextExtractor) -> None:
    fixture = FIXTURES / "sample.md"
    result = extractor.extract(fixture.read_bytes(), "sample.md", "text/markdown")
    assert "paragraph of plain text" in result.clean_text


def test_md_no_h1_returns_none_title(extractor: TextExtractor) -> None:
    content = b"---\nkey: val\n---\n\nJust a paragraph, no heading."
    result = extractor.extract(content, "no_heading.md", "text/markdown")
    assert result.title is None


def test_warnings_empty_for_clean_file(extractor: TextExtractor) -> None:
    result = extractor.extract(b"Clean content", "clean.txt", "text/plain")
    assert result.warnings == []
