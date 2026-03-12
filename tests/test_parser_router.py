"""Tests for ParserRouter hybrid routing policy.

Covers:
- Known strong formats route to the expected extractor.
- .xls is rejected cleanly with a readable error.
- Text-like alias extensions route to TextExtractor when content is text-like.
- Unknown extensions route to TextExtractor when content is text-like.
- Binary content is rejected even for strong-named formats (not applicable),
  and for text-like aliases.
"""

import pytest

from ingestion_service.app.extractors.csv_extractor import CsvExtractor
from ingestion_service.app.extractors.docx_extractor import DocxExtractor
from ingestion_service.app.extractors.pdf_extractor import PdfExtractor
from ingestion_service.app.extractors.text_extractor import TextExtractor
from ingestion_service.app.extractors.xlsx_extractor import XlsxExtractor
from ingestion_service.app.services.file_validation_service import FileValidationError
from ingestion_service.app.services.parser_router import route_parser

_TEXT_BYTES = b"This is plain text content for routing tests.\nSecond line.\n"
_BINARY_BYTES = b"\x00" * 300 + b"\xff\xfe" * 100


# ---------------------------------------------------------------------------
# Strong known formats
# ---------------------------------------------------------------------------

def test_pdf_routes_to_pdf_extractor() -> None:
    extractor = route_parser("application/pdf", "pdf", _TEXT_BYTES)
    assert isinstance(extractor, PdfExtractor)


def test_docx_routes_to_docx_extractor() -> None:
    extractor = route_parser("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx", _TEXT_BYTES)
    assert isinstance(extractor, DocxExtractor)


def test_xlsx_routes_to_xlsx_extractor() -> None:
    extractor = route_parser("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx", _TEXT_BYTES)
    assert isinstance(extractor, XlsxExtractor)


def test_csv_routes_to_csv_extractor() -> None:
    extractor = route_parser("text/csv", "csv", _TEXT_BYTES)
    assert isinstance(extractor, CsvExtractor)


def test_txt_routes_to_text_extractor() -> None:
    extractor = route_parser("text/plain", "txt", _TEXT_BYTES)
    assert isinstance(extractor, TextExtractor)


def test_md_routes_to_text_extractor() -> None:
    extractor = route_parser("text/markdown", "md", _TEXT_BYTES)
    assert isinstance(extractor, TextExtractor)


# ---------------------------------------------------------------------------
# Binary reject list
# ---------------------------------------------------------------------------

def test_xls_is_rejected_with_422_error() -> None:
    with pytest.raises(FileValidationError, match=r"\.xls.*not supported"):
        route_parser("application/vnd.ms-excel", "xls", _BINARY_BYTES)


def test_xls_rejection_recommends_xlsx() -> None:
    with pytest.raises(FileValidationError, match=r"\.xlsx"):
        route_parser("application/vnd.ms-excel", "xls", _BINARY_BYTES)


def test_exe_is_rejected() -> None:
    with pytest.raises(FileValidationError, match=r"\.exe"):
        route_parser("application/octet-stream", "exe", _BINARY_BYTES)


def test_dll_is_rejected() -> None:
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "dll", _BINARY_BYTES)


# ---------------------------------------------------------------------------
# Text-like alias extensions
# ---------------------------------------------------------------------------

def test_bat_with_text_content_routes_to_text_extractor() -> None:
    bat_content = b"@echo off\necho Hello World\npause\n"
    extractor = route_parser("text/plain", "bat", bat_content)
    assert isinstance(extractor, TextExtractor)


def test_jsx_with_text_content_routes_to_text_extractor() -> None:
    jsx_content = b"import React from 'react';\nexport default function App() { return <div/>; }\n"
    extractor = route_parser("text/plain", "jsx", jsx_content)
    assert isinstance(extractor, TextExtractor)


def test_ps1_with_text_content_routes_to_text_extractor() -> None:
    ps1_content = b"Write-Host 'Hello from PowerShell'\n"
    extractor = route_parser("text/plain", "ps1", ps1_content)
    assert isinstance(extractor, TextExtractor)


def test_json_with_text_content_routes_to_text_extractor() -> None:
    json_content = b'{"key": "value"}\n'
    extractor = route_parser("application/json", "json", json_content)
    assert isinstance(extractor, TextExtractor)


# ---------------------------------------------------------------------------
# Unknown / missing extension with text content
# ---------------------------------------------------------------------------

def test_unknown_extension_with_text_content_routes_to_text_extractor() -> None:
    extractor = route_parser("application/octet-stream", "zzz", _TEXT_BYTES)
    assert isinstance(extractor, TextExtractor)


def test_empty_extension_with_text_content_routes_to_text_extractor() -> None:
    extractor = route_parser("text/plain", "", _TEXT_BYTES)
    assert isinstance(extractor, TextExtractor)


# ---------------------------------------------------------------------------
# Unknown extension with binary content is rejected
# ---------------------------------------------------------------------------

def test_unknown_extension_with_binary_content_is_rejected() -> None:
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "zzz", _BINARY_BYTES)


def test_empty_extension_with_binary_content_is_rejected() -> None:
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "", _BINARY_BYTES)
