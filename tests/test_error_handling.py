"""Tests for structured JSON error responses.

Confirms that all error paths return JSON with the shape
{"error": "...", "detail": "..."} rather than HTML tracebacks.
"""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def use_tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect blob storage to a temp directory for each test."""
    import ingestion_service.app.config as cfg
    monkeypatch.setattr(cfg.settings, "binary_storage_path", str(tmp_path))


def _error_shape(body: dict) -> bool:
    """Return True if the response body matches the expected error shape."""
    return "error" in body and "detail" in body


def test_unsupported_extension_returns_422_json(client: TestClient) -> None:
    # Use .xls with binary content — an explicitly rejected binary format.
    binary_content = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 200
    response = client.post(
        "/ingest/file",
        files={"file": ("report.xls", io.BytesIO(binary_content), "application/vnd.ms-excel")},
        data={"client_meta": json.dumps({"original_filename": "report.xls"})},
    )
    assert response.status_code == 422
    body = response.json()
    assert _error_shape(body), f"Unexpected body: {body}"
    assert body["error"] == "FileValidationError"
    assert ".xls" in body["detail"]


def test_malformed_client_meta_returns_400(client: TestClient) -> None:
    response = client.post(
        "/ingest/file",
        files={"file": ("f.txt", io.BytesIO(b"x"), "text/plain")},
        data={"client_meta": "not-valid-json"},
    )
    assert response.status_code == 400
    # This 400 is raised via HTTPException in the route, which FastAPI converts
    # to its default {"detail": "..."} shape (not our custom handler).
    body = response.json()
    assert "detail" in body


def test_missing_file_field_returns_422(client: TestClient) -> None:
    """POSTing without a file field at all should return 422 (FastAPI validation)."""
    response = client.post(
        "/ingest/file",
        data={"client_meta": json.dumps({"original_filename": "f.txt"})},
    )
    assert response.status_code == 422


def test_error_responses_are_not_html(client: TestClient) -> None:
    """Error responses must be JSON, never HTML."""
    # Use .xls with binary content — an explicitly rejected binary format.
    binary_content = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 200
    response = client.post(
        "/ingest/file",
        files={"file": ("bad.xls", io.BytesIO(binary_content), "application/vnd.ms-excel")},
        data={"client_meta": json.dumps({"original_filename": "bad.xls"})},
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")
    body = response.text
    assert "<html" not in body.lower()
    assert "<body" not in body.lower()


def test_oversized_file_returns_422_json(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uploading a file larger than max_upload_size_mb returns 422 JSON."""
    import ingestion_service.app.config as cfg
    monkeypatch.setattr(cfg.settings, "max_upload_size_mb", 1)
    big_content = b"x" * (1024 * 1024 + 1)
    response = client.post(
        "/ingest/file",
        files={"file": ("big.txt", io.BytesIO(big_content), "text/plain")},
        data={"client_meta": json.dumps({"original_filename": "big.txt"})},
    )
    assert response.status_code == 422
    body = response.json()
    assert _error_shape(body), f"Unexpected body: {body}"
    assert "exceeds" in body["detail"]
