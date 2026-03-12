"""Tests for storage.blob_store.LocalBlobStore."""

from pathlib import Path

from vbub_doc_ingestion.storage.blob_store import LocalBlobStore


def test_put_writes_file_to_expected_path(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    content = b"hello blob"
    sha256 = "abcdef1234567890" * 4  # 64-char fake hex digest
    key = store.put(content, "report.pdf", sha256)

    expected_path = tmp_path / sha256[:8] / f"{sha256}_report.pdf"
    assert expected_path.exists()
    assert expected_path.read_bytes() == content
    assert key == f"{sha256[:8]}/{sha256}_report.pdf"


def test_get_returns_original_bytes(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    content = b"round trip check"
    sha256 = "deadbeef" * 8  # 64-char fake hex
    key = store.put(content, "notes.txt", sha256)
    assert store.get(key) == content


def test_put_creates_shard_directory(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    sha256 = "cafebabe" * 8
    store.put(b"data", "data.csv", sha256)
    shard_dir = tmp_path / sha256[:8]
    assert shard_dir.is_dir()


def test_storage_root_created_if_missing(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "storage"
    store = LocalBlobStore(nested)
    sha256 = "11223344" * 8
    store.put(b"x", "x.txt", sha256)
    assert nested.exists()


def test_filename_path_separators_sanitised(tmp_path: Path) -> None:
    """Filenames with path separators must not escape the shard directory."""
    store = LocalBlobStore(tmp_path)
    sha256 = "aabbccdd" * 8
    # Attempt path traversal via filename
    key = store.put(b"payload", "../../escape.txt", sha256)
    stored_path = tmp_path / key
    assert stored_path.exists()
    # The stored file must be inside the storage root, not above it
    assert tmp_path in stored_path.parents
