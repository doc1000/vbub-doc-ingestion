"""Tabular text policy service.

Filters rows from a parsed tabular document before flattening to text.
The goal is to suppress rows that carry no semantic value for downstream
topic modeling or RAG — typically rows composed entirely of numbers
(e.g. data-only rows in a financial spreadsheet).

Rules:
  - The first row (header) is always retained, regardless of content.
  - Any subsequent row where more than 80% of non-empty cells parse as
    a float is suppressed.
  - Rows with no non-empty cells are also suppressed.
"""


def _is_numeric(value: str) -> bool:
    """Return True if the string can be parsed as a float."""
    try:
        float(value.replace(",", ""))  # handle comma-formatted numbers
        return True
    except ValueError:
        return False


def filter_rows(rows: list[list[str]], source_type: str) -> list[list[str]]:
    """Filter tabular rows, suppressing numeric-heavy data rows.

    The header row (index 0) is always kept. Subsequent rows are kept
    only if fewer than or equal to 80% of their non-empty cells are numeric.

    Args:
        rows:        list of rows, each a list of string cell values.
        source_type: format hint, e.g. "csv" or "xlsx" (reserved for
                     future format-specific policies; not used today).

    Returns:
        Filtered list of rows suitable for flattening to readable text.
    """
    if not rows:
        return []

    result: list[list[str]] = [rows[0]]  # always keep header

    for row in rows[1:]:
        non_empty = [cell for cell in row if cell.strip()]
        if not non_empty:
            continue  # drop blank rows
        numeric_count = sum(1 for cell in non_empty if _is_numeric(cell))
        numeric_ratio = numeric_count / len(non_empty)
        if numeric_ratio <= 0.80:
            result.append(row)

    return result
