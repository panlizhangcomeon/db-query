"""
Application Configuration

Uses pydantic-settings for environment variable management.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API
    openai_api_key: str | None = None
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # SQLite database path
    db_query_sqlite_path: Path = Path.home() / ".db_query" / "db_query.db"

    # CORS
    cors_origins: str = "*"

    # Connection defaults
    connection_timeout: int = 30
    default_limit: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
