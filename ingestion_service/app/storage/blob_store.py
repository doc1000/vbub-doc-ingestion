"""Local filesystem blob store.

Responsibility: write and read original file binaries on the local filesystem.

Storage layout:
    <root>/<sha256[:8]>/<sha256>_<filename>

The first 8 hex characters of the SHA-256 are used as a sharding prefix to
avoid putting all files in a single flat directory. The full hash is part of
the filename to make accidental overwrites of different files impossible.

This is the only storage implementation for v1 local development.
In production the storage root is passed from the config (Phase 6).
The orchestrator calls LocalBlobStore directly — no wrapper service is needed.
"""

from pathlib import Path


class LocalBlobStore:
    """Writes and reads immutable binary blobs on the local filesystem.

    Args:
        storage_root: path to the root directory under which blobs are stored.
                      Created automatically if it does not exist.
    """

    def __init__(self, storage_root: str | Path) -> None:
        self._root = Path(storage_root)

    def put(self, file_bytes: bytes, filename: str, sha256: str) -> str:
        """Write bytes to the store and return a storage key.

        The storage key is a relative path from the storage root, e.g.
        'ab12cd34/ab12cd34ef56...._report.pdf'.  It is stable: the same
        file always maps to the same key.

        Args:
            file_bytes: raw bytes to store.
            filename:   original filename; included in the stored path for
                        human readability.
            sha256:     hex-encoded SHA-256 digest of file_bytes.

        Returns:
            Relative storage key string.
        """
        shard = sha256[:8]
        # Sanitise filename: replace path separators to prevent directory
        # traversal when the key is later joined back to the root.
        safe_name = Path(filename).name
        dest_dir = self._root / shard
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{sha256}_{safe_name}"
        dest_file.write_bytes(file_bytes)
        # Return a relative key (forward slashes for portability).
        return f"{shard}/{sha256}_{safe_name}"

    def get(self, storage_key: str) -> bytes:
        """Read and return the bytes stored under storage_key.

        Args:
            storage_key: relative key returned by a previous put() call.

        Returns:
            Raw bytes of the stored file.

        Raises:
            FileNotFoundError: if the key does not exist in the store.
        """
        return (self._root / storage_key).read_bytes()
