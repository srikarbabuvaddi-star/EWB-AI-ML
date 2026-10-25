"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    PROJECT_NAME: str = "Students Database CRUD API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "A robust, production-grade RESTful API to manage student records "
        "built with FastAPI, SQLAlchemy, and SQLite."
    )
    DATABASE_URL: str = "sqlite:///./students.db"
    CORS_ORIGINS: List[str] = ["*"]
    DEFAULT_PAGE_LIMIT: int = 10
    MAX_PAGE_LIMIT: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
