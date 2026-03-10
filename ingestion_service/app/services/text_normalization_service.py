"""Text normalisation service.

Applies a deterministic set of cleanup operations to raw extracted text.
Called once per document, after extraction, before assembly.

Transformations applied (in order):
  1. Unicode NFC normalisation
  2. Windows line endings (\r\n) and bare \r -> \n
  3. Collapse three or more consecutive blank lines to two blank lines
  4. Strip trailing whitespace from every line
  5. Normalise smart quotes and typographic dashes to ASCII equivalents
"""

import re
import unicodedata

# Three or more consecutive blank lines (lines containing only whitespace).
_EXCESS_BLANK_LINES_RE = re.compile(r"(\n\s*){3,}\n")

# Smart quotes and typographic dashes mapped to ASCII equivalents.
_SMART_CHAR_MAP: dict[str, str] = {
    "\u2018": "'",   # left single quotation mark
    "\u2019": "'",   # right single quotation mark
    "\u201c": '"',   # left double quotation mark
    "\u201d": '"',   # right double quotation mark
    "\u2013": "-",   # en dash
    "\u2014": "--",  # em dash
    "\u2026": "...", # horizontal ellipsis
}
_SMART_CHAR_TABLE = str.maketrans(_SMART_CHAR_MAP)


def normalize_text(raw_text: str) -> str:
    """Normalise raw extracted text into clean, consistent plain text.

    Args:
        raw_text: text as returned by an extractor (pre-normalisation).

    Returns:
        Cleaned string with consistent encoding, line endings, spacing,
        and ASCII-equivalent punctuation.
    """
    # 1. Unicode NFC
    text = unicodedata.normalize("NFC", raw_text)

    # 2. Normalise line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Strip trailing whitespace from each line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # 4. Collapse excess blank lines (3+ consecutive blank lines -> 2 blank lines)
    # Two blank lines = three newlines in a row (\n\n\n).
    # The regex matches three or more \n (possibly with spaces) and replaces with \n\n\n.
    text = re.sub(r"\n{3,}", "\n\n\n", text)

    # 5. Normalise smart quotes and typographic dashes
    text = text.translate(_SMART_CHAR_TABLE)

    return text
