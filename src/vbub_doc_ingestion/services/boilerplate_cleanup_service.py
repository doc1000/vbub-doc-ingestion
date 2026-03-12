"""Boilerplate cleanup service.

Removes repeated headers, footers, and page numbers from extracted PDF text.
For all non-PDF MIME types the function returns the text unchanged.

Algorithm (PDF only):
  1. Split the text into page blocks on double-newline boundaries.
  2. Collect the first and last non-empty line of each page block.
  3. Any line that appears verbatim as the first OR last line of 3 or more
     page blocks is treated as a repeated header or footer and removed
     wherever it appears at the start or end of a block.
  4. Lines consisting only of digits (page numbers) are removed from
     every block.
  5. Re-join the cleaned blocks with double newlines.

Limitations:
  - Only handles simple verbatim repetition; does not catch varying
    page numbers embedded in otherwise-repeated header strings.
  - False positives are possible on very short documents (<3 pages).
"""

import re
from collections import Counter

_PDF_MIME = "application/pdf"
_DIGITS_ONLY_RE = re.compile(r"^\s*\d+\s*$")


def _split_pages(text: str) -> list[list[str]]:
    """Split text into pages (double-newline blocks), each as a list of lines."""
    raw_blocks = re.split(r"\n{2,}", text)
    return [block.splitlines() for block in raw_blocks if block.strip()]


def _find_repeated_boundary_lines(pages: list[list[str]], threshold: int = 3) -> set[str]:
    """Return lines that appear verbatim in the first or last 3 non-empty lines
    of >= threshold pages.

    Checking the last 3 lines (not just the very last) handles the common case
    where a page number sits below a repeated footer line.
    """
    _BOUNDARY_WINDOW = 3

    candidate_counts: Counter = Counter()

    for lines in pages:
        non_empty = [l for l in lines if l.strip()]
        head = non_empty[:_BOUNDARY_WINDOW]
        tail = non_empty[-_BOUNDARY_WINDOW:] if len(non_empty) > _BOUNDARY_WINDOW else []
        for line in set(head + tail):
            candidate_counts[line] += 1

    return {line for line, count in candidate_counts.items() if count >= threshold}


def _clean_page(lines: list[str], repeated: set[str]) -> list[str]:
    """Remove repeated boundary lines and digit-only lines from a page."""
    result: list[str] = []
    for line in lines:
        if _DIGITS_ONLY_RE.match(line):
            continue
        if line in repeated:
            continue
        result.append(line)
    return result


def remove_boilerplate(text: str, mime: str) -> str:
    """Remove repeated headers, footers, and page numbers from PDF text.

    For non-PDF MIME types, returns text unchanged.

    Args:
        text: raw extracted text (output of the extractor).
        mime: canonical MIME type of the document.

    Returns:
        Cleaned text string.
    """
    if mime != _PDF_MIME:
        return text

    pages = _split_pages(text)
    if not pages:
        return text

    repeated = _find_repeated_boundary_lines(pages)
    cleaned_pages = [_clean_page(lines, repeated) for lines in pages]

    return "\n\n".join(
        "\n".join(lines)
        for lines in cleaned_pages
        if any(l.strip() for l in lines)
    )
