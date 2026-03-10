"""Tests for the health endpoint and the Phase 1 ingest stub."""

import io
import json

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_file_stub_returns_501(client: TestClient) -> None:
    """Phase 1: the ingest endpoint is wired but not yet implemented."""
    client_meta = json.dumps({"original_filename": "test.txt"})
    response = client.post(
        "/ingest/file",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"client_meta": client_meta},
    )
    assert response.status_code == 501
