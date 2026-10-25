"""Pytest configuration and fixtures for testing with an isolated SQLite database."""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Create in-memory SQLite database engine with StaticPool to keep state alive across connections
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean, isolated database session for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient fixture with get_db dependency overridden to the test database session."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_student_data() -> dict:
    """Fixture providing a standard valid student data dictionary."""
    return {
        "name": "Jane Doe",
        "date_of_birth": "2001-05-15",
        "email": "jane.doe@example.edu",
        "phone": "+1 555-0144",
        "course": "Computer Science",
        "address": "456 University Ave, Campus View",
        "enrollment_date": "2024-09-01",
    }


@pytest.fixture
def sample_student_data_2() -> dict:
    """Fixture providing a second distinct valid student data dictionary."""
    return {
        "name": "John Smith",
        "date_of_birth": "2000-11-20",
        "email": "john.smith@example.edu",
        "phone": "+1 555-0188",
        "course": "Data Science",
        "address": "789 College Boulevard",
        "enrollment_date": "2024-09-01",
    }
