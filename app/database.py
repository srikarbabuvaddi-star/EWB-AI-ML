"""Database configuration, engine setup, and session management."""

import logging
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

logger = logging.getLogger(__name__)

# Configure connect_args for SQLite thread safety
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

    # Ensure parent directory exists for file-based SQLite databases (e.g. /tmp on Vercel)
    if ":///" in settings.DATABASE_URL and not settings.DATABASE_URL.startswith("sqlite:///:memory:"):
        db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
        try:
            db_dir = Path(db_path_str).parent
            if db_dir and not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as dir_err:
            logger.warning("Could not pre-create database directory: %s", dir_err)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

# Create SessionLocal class with autocommit=False and autoflush=False
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# Declarative Base for ORM models
Base = declarative_base()

_initialized = False


def init_db() -> None:
    """Initialize database tables without modifying or wiping existing records.

    Ensures tables exist on application startup while maintaining persistence across restarts.
    """
    global _initialized
    if _initialized:
        return
    try:
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=engine)
        _initialized = True
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database schema: %s", exc)
        raise


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an isolated SQLAlchemy database session per request.

    Includes lazy schema verification for serverless environments.
    """
    global _initialized
    if not _initialized:
        try:
            init_db()
        except Exception as exc:
            logger.warning("Lazy database initialization warning: %s", exc)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
