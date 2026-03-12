"""Text extractor for plain text (.txt) and Markdown (.md) files.

Handles:
  - UTF-8 with or without BOM
  - latin-1 fallback on decode error
  - YAML front matter stripping for .md files (--- delimited block)
  - Title extraction:
      .md  — first line matching ^# <text>
      .txt — first non-empty line

Returns an ExtractionResult with raw (un-normalised) text.
Normalisation is performed by text_normalization_service in a separate step.
"""

import re
from pathlib import Path

from vbub_doc_ingestion.domain.contracts import ExtractionResult

_PARSER_NAME = "TextExtractor"
_PARSER_VERSION = "0.1.0"

_YAML_FRONT_MATTER_RE = re.compile(
    r"^\s*---\s*\n.*?\n---\s*\n?",
    re.DOTALL,
)

_MD_H1_RE = re.compile(r"^\s*#\s+(.+)")


def _decode(file_bytes: bytes) -> str:
    """Decode bytes to str.  Tries UTF-8 (with BOM), then falls back to latin-1."""
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _strip_yaml_front_matter(text: str) -> str:
    """Remove a YAML front matter block from the start of a markdown string."""
    return _YAML_FRONT_MATTER_RE.sub("", text, count=1)


def _extract_md_title(text: str) -> str | None:
    """Return text of the first H1 heading, or None if none found."""
    for line in text.splitlines():
        m = _MD_H1_RE.match(line)
        if m:
            return m.group(1).strip()
    return None


def _extract_txt_title(text: str) -> str | None:
    """Return the first non-empty line as the title, or None."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


class TextExtractor:
    """Extracts text from plain .txt and .md files.

    Implements the DocumentExtractor Protocol.
    """

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        canonical_mime: str,
    ) -> ExtractionResult:
        """Decode and extract text from a plain-text or markdown file.

        Args:
            file_bytes:     raw bytes of the file.
            filename:       used to determine whether to apply markdown rules.
            canonical_mime: not used for dispatch here; extension drives behaviour.

        Returns:
            ExtractionResult with raw text (pre-normalisation) and optional title.
        """
        extension = Path(filename).suffix.lstrip(".").lower()
        raw = _decode(file_bytes)

        if extension == "md":
            body = _strip_yaml_front_matter(raw)
            title = _extract_md_title(body)
        else:
            body = raw
            title = _extract_txt_title(body)

        return ExtractionResult(
            parser_name=_PARSER_NAME,
            parser_version=_PARSER_VERSION,
            title=title,
            clean_text=body,
            warnings=[],
        )
