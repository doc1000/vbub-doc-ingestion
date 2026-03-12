"""Tests for content_classification_service: is_probably_text() heuristic."""

import pytest

from ingestion_service.app.services.content_classification_service import (
    BINARY_REJECT_EXTENSIONS,
    TEXT_LIKE_EXTENSIONS,
    is_probably_text,
)


# ---------------------------------------------------------------------------
# is_probably_text — text samples
# ---------------------------------------------------------------------------

def test_plain_ascii_is_text() -> None:
    assert is_probably_text(b"Hello, world!\nThis is a plain-text file.\n") is True


def test_utf8_content_is_text() -> None:
    assert is_probably_text("Héllo wörld — Unicode content.".encode("utf-8")) is True


def test_multiline_script_is_text() -> None:
    script = b"#!/usr/bin/env python3\n\nprint('hello')\n"
    assert is_probably_text(script) is True


def test_empty_bytes_returns_true() -> None:
    assert is_probably_text(b"") is True


def test_json_content_is_text() -> None:
    data = b'{"key": "value", "number": 42, "flag": true}'
    assert is_probably_text(data) is True


# ---------------------------------------------------------------------------
# is_probably_text — binary / non-text samples
# ---------------------------------------------------------------------------

def test_null_byte_heavy_content_is_not_text() -> None:
    # Simulate a binary file: many null bytes.
    binary = b"\x00" * 200 + b"some text"
    assert is_probably_text(binary) is False


def test_non_utf8_high_bytes_is_not_text() -> None:
    # Bytes that are not valid UTF-8 and not printable.
    binary = bytes(range(128, 256)) * 10
    assert is_probably_text(binary) is False


def test_mixed_null_bytes_exceeds_threshold() -> None:
    # 5% null bytes — exceeds the 1% threshold.
    sample = b"abcde\x00abcde\x00" * 50  # ~8% nulls
    assert is_probably_text(sample) is False


# ---------------------------------------------------------------------------
# Extension sets
# ---------------------------------------------------------------------------

def test_text_like_extensions_contains_expected_members() -> None:
    for ext in ("txt", "md", "bat", "jsx", "py", "json", "yaml", "sh"):
        assert ext in TEXT_LIKE_EXTENSIONS, f"Expected '{ext}' in TEXT_LIKE_EXTENSIONS"


def test_binary_reject_extensions_contains_xls() -> None:
    assert "xls" in BINARY_REJECT_EXTENSIONS


def test_binary_reject_extensions_minimal() -> None:
    # Verify the reject set stays small (no accidental expansion).
    assert len(BINARY_REJECT_EXTENSIONS) <= 10


def test_strong_formats_not_in_text_like() -> None:
    # pdf, docx, xlsx, csv are not text-like aliases; they have dedicated extractors.
    for ext in ("pdf", "docx", "xlsx", "csv"):
        assert ext not in TEXT_LIKE_EXTENSIONS, (
            f"'{ext}' should not be in TEXT_LIKE_EXTENSIONS; it has its own extractor"
        )
