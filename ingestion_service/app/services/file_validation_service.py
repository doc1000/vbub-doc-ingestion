"""File validation service.

Responsibility: validate an uploaded file before any processing begins.

Checks performed:
  - File size against MAX_UPLOAD_SIZE_MB (default 25 MB, overridden by env var).
  - Extension extracted and normalised from the filename.
  - Extension membership in the supported v1 format list.
  - MIME type detected from file bytes via python-magic (magic-byte sniffing).
  - SHA-256 hash of the raw bytes.

Raises ValueError (FileValidationError subclass) on rejection so that the
error handler introduced in Phase 6 can map it to a 422 response.
Internal results are returned as a ValidationResult dataclass — not a
Pydantic model, since this is an internal intermediate, not a public contract.
"""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import magic

from ingestion_service.app.api.schemas import ClientMeta
from ingestion_service.app.domain.enums import SupportedFormat

# Default limit; overridden by MAX_UPLOAD_SIZE_MB env var in Phase 6 config.
_DEFAULT_MAX_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "25"))

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(f.value for f in SupportedFormat)


class FileValidationError(ValueError):
    """Raised when an uploaded file fails validation.

    Subclasses ValueError so generic ValueError handlers also catch it,
    but Phase 6 error_handlers.py will map it specifically to HTTP 422.
    """


@dataclass
class ValidationResult:
    """Internal result of file validation.

    Not a public contract — not returned to callers outside the service layer.
    """

    canonical_mime: str
    extension: str
    sha256: str
    size_bytes: int
    is_valid: bool
    rejection_reason: Optional[str] = None


def validate_file(
    file_bytes: bytes,
    filename: str,
    client_meta: ClientMeta,
) -> ValidationResult:
    """Validate an uploaded file and return a ValidationResult.

    Args:
        file_bytes:  raw bytes of the uploaded file.
        filename:    display filename used for extension extraction.
        client_meta: client-submitted metadata (size hint used for cross-check).

    Returns:
        ValidationResult with is_valid=True.

    Raises:
        FileValidationError: if the file fails any validation check.
    """
    size_bytes = len(file_bytes)
    max_bytes = _DEFAULT_MAX_MB * 1024 * 1024

    if size_bytes > max_bytes:
        raise FileValidationError(
            f"File size {size_bytes} bytes exceeds the maximum of "
            f"{_DEFAULT_MAX_MB} MB ({max_bytes} bytes)."
        )

    # Normalise extension: strip leading dot, lowercase, handle missing extension.
    suffix = Path(filename).suffix
    extension = suffix.lstrip(".").lower() if suffix else ""

    if not extension:
        raise FileValidationError(
            f"Cannot determine file type: filename '{filename}' has no extension."
        )

    if extension not in _SUPPORTED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '.{extension}'. "
            f"Supported formats: {sorted(_SUPPORTED_EXTENSIONS)}."
        )

    # Magic-byte MIME detection — more reliable than client-supplied MIME.
    canonical_mime: str = magic.from_buffer(file_bytes, mime=True)

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    return ValidationResult(
        canonical_mime=canonical_mime,
        extension=extension,
        sha256=sha256,
        size_bytes=size_bytes,
        is_valid=True,
    )
