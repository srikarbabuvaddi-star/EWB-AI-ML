"""Application configuration using Pydantic Settings."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_database_url() -> str:
    """Return appropriate SQLite location based on deployment environment.

    On Vercel/serverless platforms, the root filesystem is read-only, so the SQLite
    database must be placed in the writable `/tmp` directory.
    """
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite:////tmp/students.db"
    return "sqlite:///./students.db"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    PROJECT_NAME: str = "Students Database CRUD API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "A robust, production-grade RESTful API to manage student records "
        "built with FastAPI, SQLAlchemy, and SQLite."
    )
    DATABASE_URL: str = get_default_database_url()
    CORS_ORIGINS: List[str] = ["*"]
    DEFAULT_PAGE_LIMIT: int = 10
    MAX_PAGE_LIMIT: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
