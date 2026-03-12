"""Tests for text-like alias routing.

Confirms that files with text-like but non-standard extensions (.bat, .jsx, etc.)
or suffixless filenames containing plain-text content are routed to TextExtractor
and produce a valid ExtractionResult.
"""

import pytest

from vbub_doc_ingestion.extractors.text_extractor import TextExtractor
from vbub_doc_ingestion.services.file_validation_service import FileValidationError
from vbub_doc_ingestion.services.parser_router import route_parser


def _route_and_extract(content: bytes, filename: str, extension: str) -> None:
    """Helper: route then extract; assert TextExtractor is selected."""
    extractor = route_parser("text/plain", extension, content)
    assert isinstance(extractor, TextExtractor)
    result = extractor.extract(content, filename, "text/plain")
    assert result.clean_text.strip() != ""
    assert result.parser_name == "TextExtractor"


def test_bat_file_routes_and_extracts() -> None:
    content = b"@echo off\necho Running batch file\npause\n"
    _route_and_extract(content, "run.bat", "bat")


def test_jsx_file_routes_and_extracts() -> None:
    content = b"import React from 'react';\nexport const Component = () => <div>Hello</div>;\n"
    _route_and_extract(content, "Component.jsx", "jsx")


def test_ps1_file_routes_and_extracts() -> None:
    content = b"$name = 'World'\nWrite-Host \"Hello $name\"\n"
    _route_and_extract(content, "script.ps1", "ps1")


def test_yaml_file_routes_and_extracts() -> None:
    content = b"name: test\nversion: 1.0\ndescription: A YAML config file\n"
    _route_and_extract(content, "config.yaml", "yaml")


def test_toml_file_routes_and_extracts() -> None:
    content = b"[package]\nname = \"myapp\"\nversion = \"0.1.0\"\n"
    _route_and_extract(content, "Cargo.toml", "toml")


def test_ini_file_routes_and_extracts() -> None:
    content = b"[section]\nkey=value\n"
    _route_and_extract(content, "settings.ini", "ini")


def test_log_file_routes_and_extracts() -> None:
    content = b"2026-03-11 INFO Application started\n2026-03-11 INFO Processing complete\n"
    _route_and_extract(content, "app.log", "log")


def test_sh_file_routes_and_extracts() -> None:
    content = b"#!/bin/bash\necho 'hello from shell'\n"
    _route_and_extract(content, "deploy.sh", "sh")


def test_suffixless_text_file_routes_to_text_extractor() -> None:
    """A file with no extension but text content should reach TextExtractor."""
    content = b"This is a plain text document with no file extension.\n"
    extractor = route_parser("text/plain", "", content)
    assert isinstance(extractor, TextExtractor)
    result = extractor.extract(content, "README", "text/plain")
    assert "plain text document" in result.clean_text


def test_unknown_extension_text_file_routes_to_text_extractor() -> None:
    """An unknown extension with text content is accepted via heuristic."""
    content = b"Memo: all hands meeting on Friday at 2pm.\n"
    extractor = route_parser("application/octet-stream", "memo", content)
    assert isinstance(extractor, TextExtractor)
