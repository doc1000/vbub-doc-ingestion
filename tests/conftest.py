"""Shared pytest fixtures for the ingestion service test suite."""

import pytest
from fastapi.testclient import TestClient

from ingestion_service.app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Return a synchronous TestClient bound to the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)
