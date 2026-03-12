"""Tests for text_normalization_service.normalize_text()."""

import unicodedata

from vbub_doc_ingestion.services.text_normalization_service import normalize_text


def test_crlf_converted_to_lf() -> None:
    result = normalize_text("line one\r\nline two\r\nline three")
    assert "\r" not in result
    assert result == "line one\nline two\nline three"


def test_bare_cr_converted_to_lf() -> None:
    result = normalize_text("line one\rline two")
    assert "\r" not in result
    assert "line one\nline two" == result


def test_excess_blank_lines_collapsed() -> None:
    text = "para one\n\n\n\n\npara two"
    result = normalize_text(text)
    # No more than two consecutive blank lines (three \n in a row)
    assert "\n\n\n\n" not in result
    assert "para one" in result
    assert "para two" in result


def test_trailing_whitespace_stripped() -> None:
    result = normalize_text("hello   \nworld  ")
    lines = result.splitlines()
    assert lines[0] == "hello"
    assert lines[1] == "world"


def test_unicode_nfc_normalisation() -> None:
    # "é" can be represented as a single codepoint (NFC) or as e + combining accent (NFD).
    nfd = unicodedata.normalize("NFD", "\u00e9")
    result = normalize_text(nfd)
    assert unicodedata.is_normalized("NFC", result)
    assert "\u00e9" in result


def test_smart_quotes_replaced() -> None:
    result = normalize_text("\u201cHello\u201d and \u2018world\u2019")
    assert '"Hello"' in result
    assert "'world'" in result
    assert "\u201c" not in result
    assert "\u201d" not in result


def test_em_dash_replaced() -> None:
    result = normalize_text("before\u2014after")
    assert "--" in result
    assert "\u2014" not in result


def test_en_dash_replaced() -> None:
    result = normalize_text("10\u201320")
    assert "-" in result
    assert "\u2013" not in result


def test_ellipsis_replaced() -> None:
    result = normalize_text("wait\u2026")
    assert "..." in result
    assert "\u2026" not in result


def test_empty_string_returns_empty() -> None:
    assert normalize_text("") == ""


def test_already_clean_text_unchanged_structure() -> None:
    clean = "First line\n\nSecond paragraph"
    result = normalize_text(clean)
    assert "First line" in result
    assert "Second paragraph" in result
