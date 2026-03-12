"""Tests for file_validation_service.validate_file."""

import hashlib

import pytest

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.services.file_validation_service import (
    FileValidationError,
    validate_file,
)

_CLIENT_META = ClientMeta(original_filename="sample.txt")


def _meta(filename: str) -> ClientMeta:
    return ClientMeta(original_filename=filename)


def test_valid_txt_returns_result() -> None:
    content = b"Hello, world."
    result = validate_file(content, "sample.txt", _meta("sample.txt"))
    assert result.is_valid is True
    assert result.extension == "txt"
    assert result.size_bytes == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()


def test_extension_normalised_to_lowercase() -> None:
    result = validate_file(b"hi", "NOTES.TXT", _meta("NOTES.TXT"))
    assert result.extension == "txt"


def test_unsupported_extension_passes_validation() -> None:
    """Phase 7: extension filtering moved to ParserRouter; validation now accepts any extension."""
    result = validate_file(b"data", "archive.zip", _meta("archive.zip"))
    assert result.extension == "zip"
    assert result.is_valid is True


def test_missing_extension_passes_validation() -> None:
    """Phase 7: files with no extension pass validation; router decides what to do."""
    result = validate_file(b"data", "noextension", _meta("noextension"))
    assert result.extension == ""
    assert result.is_valid is True


def test_oversized_file_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch the settings singleton so the validation reads a 1 MB limit.
    import ingestion_service.app.config as cfg
    monkeypatch.setattr(cfg.settings, "max_upload_size_mb", 1)
    big = b"x" * (1024 * 1024 + 1)
    with pytest.raises(FileValidationError, match="exceeds the maximum"):
        validate_file(big, "big.txt", _meta("big.txt"))


def test_sha256_matches_known_value() -> None:
    content = b"deterministic"
    expected = hashlib.sha256(content).hexdigest()
    result = validate_file(content, "file.txt", _meta("file.txt"))
    assert result.sha256 == expected


def test_canonical_mime_detected() -> None:
    result = validate_file(b"plain text", "doc.txt", _meta("doc.txt"))
    assert "text" in result.canonical_mime
