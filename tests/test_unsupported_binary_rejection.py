"""Tests for unsupported binary file rejection.

Confirms that:
- Binary content mislabeled with a text-like extension is NOT routed to TextExtractor.
- Known binary formats (.xls, .exe, .dll) are rejected with FileValidationError.
- The error response shape is JSON-serialisable (tested via error handler mapping).
"""

import pytest

from vbub_doc_ingestion.services.file_validation_service import FileValidationError
from vbub_doc_ingestion.services.parser_router import route_parser

# Simulated binary content: many null bytes plus high-byte sequences.
_BINARY_BLOB = b"\x00\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 300 + b"\xff\xfe" * 100
# Simulate a Windows .bat file that actually contains binary bytes.
_FAKE_BAT_BINARY = b"\x4d\x5a\x00\x00" + b"\x00" * 200  # MZ header + nulls


def test_binary_bat_mislabeled_is_rejected() -> None:
    with pytest.raises(FileValidationError, match="binary"):
        route_parser("text/plain", "bat", _FAKE_BAT_BINARY)


def test_binary_jsx_mislabeled_is_rejected() -> None:
    with pytest.raises(FileValidationError, match="binary"):
        route_parser("text/plain", "jsx", _BINARY_BLOB)


def test_binary_ps1_mislabeled_is_rejected() -> None:
    with pytest.raises(FileValidationError, match="binary"):
        route_parser("text/plain", "ps1", _FAKE_BAT_BINARY)


def test_binary_json_mislabeled_is_rejected() -> None:
    with pytest.raises(FileValidationError, match="binary"):
        route_parser("application/json", "json", _BINARY_BLOB)


def test_xls_is_rejected_with_clear_message() -> None:
    with pytest.raises(FileValidationError) as exc_info:
        route_parser("application/vnd.ms-excel", "xls", _BINARY_BLOB)
    message = str(exc_info.value)
    assert ".xls" in message
    assert "not supported" in message.lower()


def test_xls_rejection_recommends_xlsx() -> None:
    with pytest.raises(FileValidationError) as exc_info:
        route_parser("application/vnd.ms-excel", "xls", _BINARY_BLOB)
    assert ".xlsx" in str(exc_info.value)


def test_exe_is_rejected_with_clear_message() -> None:
    with pytest.raises(FileValidationError) as exc_info:
        route_parser("application/octet-stream", "exe", _BINARY_BLOB)
    assert ".exe" in str(exc_info.value)


def test_dll_is_rejected() -> None:
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "dll", _BINARY_BLOB)


def test_bin_is_rejected() -> None:
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "bin", _BINARY_BLOB)


def test_rejection_error_is_file_validation_error_subclass() -> None:
    """FileValidationError must be a subclass of ValueError for error handler mapping."""
    assert issubclass(FileValidationError, ValueError)


def test_binary_content_unknown_extension_is_rejected() -> None:
    """Binary content with an unrecognised extension must not reach TextExtractor."""
    with pytest.raises(FileValidationError):
        route_parser("application/octet-stream", "xyz", _BINARY_BLOB)
