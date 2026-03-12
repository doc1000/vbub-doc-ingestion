"""Verify the FastAPI adapter works against the new package structure."""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adapters.fastapi_app.main import app


@pytest.fixture()
def adapter_client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def use_tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import vbub_doc_ingestion.config as cfg
    monkeypatch.setattr(cfg.settings, "binary_storage_path", str(tmp_path))


def test_health_returns_200(adapter_client: TestClient) -> None:
    response = adapter_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_txt_returns_200(adapter_client: TestClient) -> None:
    meta = {"original_filename": "adapter_test.txt"}
    response = adapter_client.post(
        "/ingest/file",
        files={"file": ("adapter_test.txt", io.BytesIO(b"Adapter test content"), "text/plain")},
        data={"client_meta": json.dumps(meta)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["documentId"].startswith("doc_")
    assert payload["status"] == "ready_for_indexing"
    assert "Adapter test content" in payload["extraction"]["cleanText"]
