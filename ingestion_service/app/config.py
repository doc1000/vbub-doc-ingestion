"""Centralised service configuration.

All runtime settings are read once at import time from environment
variables (or a .env file if pydantic-settings finds one).

Usage anywhere in the service:
    from ingestion_service.app.config import settings
    settings.max_upload_size_mb

Environment variables use the same names, uppercased:
    MAX_UPLOAD_SIZE_MB=10
    BINARY_STORAGE_PATH=/data/blobs
    APP_ENV=production
    LOG_LEVEL=info
    SERVICE_NAME=vbub-doc-ingestion
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service-wide configuration loaded from environment variables.

    All fields have sensible defaults for local development.
    Override any field by setting the corresponding environment variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "info"
    max_upload_size_mb: int = 25
    binary_storage_path: str = "./data/blobs"
    service_name: str = "vbub-doc-ingestion"


settings = Settings()
