"""Content classification helpers used by ParserRouter.

Provides lightweight, dependency-free heuristics to determine whether a file
should be treated as plain text or rejected as binary, independent of file suffix.

Public API:
    TEXT_LIKE_EXTENSIONS  — frozenset of extensions that are considered text-like aliases.
    BINARY_REJECT_EXTENSIONS — frozenset of known binary formats that must never reach TextExtractor.
    is_probably_text(file_bytes) — byte-level heuristic; returns True if the content looks like text.
"""

# Extensions treated as plain-text aliases.  Files with these suffixes will be
# routed to TextExtractor *only if* is_probably_text() also confirms the content.
TEXT_LIKE_EXTENSIONS: frozenset[str] = frozenset({
    "txt", "md", "bat", "ps1", "py", "js", "jsx", "ts", "tsx",
    "json", "yaml", "yml", "toml", "ini", "cfg", "conf",
    "log", "sql", "xml", "html", "css", "sh", "env",
})

# Known binary formats that must never fall through to TextExtractor.
# Keep minimal and conservative.
BINARY_REJECT_EXTENSIONS: frozenset[str] = frozenset({
    "xls", "exe", "dll", "bin", "dat",
})

# Byte window inspected for text heuristics; 8 KB is sufficient for most files.
_SAMPLE_WINDOW = 8192

# Ratio of null bytes above which the sample is considered binary.
_NULL_BYTE_RATIO_THRESHOLD = 0.01

# Minimum ratio of printable characters (after UTF-8 decode) to consider text.
_PRINTABLE_RATIO_THRESHOLD = 0.85


def is_probably_text(file_bytes: bytes) -> bool:
    """Return True if the byte content looks like plain text.

    Heuristic steps:
    1. Inspect only the first _SAMPLE_WINDOW bytes.
    2. Empty input is treated as text (empty files are allowed elsewhere).
    3. Reject if null-byte ratio exceeds _NULL_BYTE_RATIO_THRESHOLD.
    4. Attempt UTF-8 decode; reject on failure.
    5. Compute printable-character ratio; accept if >= _PRINTABLE_RATIO_THRESHOLD.

    Args:
        file_bytes: raw bytes of the file (full content or partial).

    Returns:
        True if the sample looks like human-readable text; False otherwise.
    """
    sample = file_bytes[:_SAMPLE_WINDOW]

    if not sample:
        return True

    null_count = sample.count(b"\x00")
    if null_count / len(sample) > _NULL_BYTE_RATIO_THRESHOLD:
        return False

    try:
        text = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False

    printable_count = sum(
        1 for ch in text
        if ch.isprintable() or ch in ("\n", "\r", "\t")
    )
    printable_ratio = printable_count / len(text) if text else 1.0

    return printable_ratio >= _PRINTABLE_RATIO_THRESHOLD
