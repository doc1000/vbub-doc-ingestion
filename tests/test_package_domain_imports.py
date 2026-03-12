"""Verify that domain models are importable from the new package paths."""

from vbub_doc_ingestion.domain.contracts import (
    BinaryRef,
    CanonicalDocument,
    DocumentMetadata,
    ExtractionResult,
    SourceLocator,
)
from vbub_doc_ingestion.domain.enums import IngestionStatus, SupportedFormat
from vbub_doc_ingestion.domain.schemas import ClientMeta


def test_canonical_document_importable() -> None:
    assert CanonicalDocument is not None


def test_client_meta_importable() -> None:
    meta = ClientMeta(original_filename="test.txt")
    assert meta.original_filename == "test.txt"


def test_enums_importable() -> None:
    assert SupportedFormat.pdf.value == "pdf"
    assert IngestionStatus.ready_for_indexing.value == "ready_for_indexing"


def test_canonical_document_schema_unchanged() -> None:
    """The CanonicalDocument field set must match the original contract."""
    expected_fields = {
        "document_id", "display_name", "canonical_mime", "extension",
        "binary_ref", "source_locator", "extraction", "metadata", "status",
    }
    assert set(CanonicalDocument.model_fields.keys()) == expected_fields
