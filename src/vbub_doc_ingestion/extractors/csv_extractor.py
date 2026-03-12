"""CSV extractor using Python stdlib csv.

Decodes the raw bytes, sniffs the CSV dialect, reads all rows,
applies the tabular text policy (numeric suppression), and flattens
remaining rows to pipe-delimited lines.

Title is taken from the first cell of the header row if non-empty,
otherwise None.
"""

import csv
import io

from vbub_doc_ingestion.domain.contracts import ExtractionResult
from vbub_doc_ingestion.services.tabular_text_policy_service import filter_rows

_PARSER_NAME = "CsvExtractor"
_PARSER_VERSION = "0.1.0"
_CELL_SEPARATOR = " | "


def _decode(file_bytes: bytes) -> str:
    """Decode CSV bytes as UTF-8 (with BOM), falling back to latin-1."""
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _flatten_rows(rows: list[list[str]]) -> str:
    """Join each row's cells with ' | ' and join rows with newlines."""
    return "\n".join(_CELL_SEPARATOR.join(cell.strip() for cell in row) for row in rows)


class CsvExtractor:
    """Extracts readable text from CSV files.

    Implements the DocumentExtractor Protocol.
    """

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        canonical_mime: str,
    ) -> ExtractionResult:
        """Decode, parse, filter, and flatten a CSV file to text.

        Args:
            file_bytes:     raw bytes of the CSV file.
            filename:       original filename (informational).
            canonical_mime: not used for dispatch here.

        Returns:
            ExtractionResult with pipe-delimited clean_text and optional title.
        """
        text = _decode(file_bytes)
        sample = text[:4096]

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel  # type: ignore[assignment]

        reader = csv.reader(io.StringIO(text), dialect)
        rows = [row for row in reader if any(cell.strip() for cell in row)]

        filtered = filter_rows(rows, source_type="csv")

        title: str | None = None
        if filtered and filtered[0]:
            candidate = filtered[0][0].strip()
            if candidate:
                title = candidate

        clean_text = _flatten_rows(filtered)

        return ExtractionResult(
            parser_name=_PARSER_NAME,
            parser_version=_PARSER_VERSION,
            title=title,
            clean_text=clean_text,
            warnings=[],
        )
