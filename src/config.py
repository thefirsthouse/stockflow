from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "Stockflow API"
    project_version: str = "0.1.0-dev"

    app_env: str = "development"
    debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = "sqlite+aiosqlite:///./database.db"
    sql_echo: bool = False

    secret_key: str = "change-me-in-prod"
    algorithm: str = "HS256"
    acces_token_expire_minutes: int = 30

settings = Settings()
