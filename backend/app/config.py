from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "File Cabinet"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/app.db"
    storage_dir: Path = Path("data/storage")
    max_upload_mb: int = 500
    cleanup_interval_minutes: int = 30
    keep_hours: int = 24
    public_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
