"""System health check and welcome routers."""

from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import HealthCheckResponse, WelcomeResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


@router.get(
    "/",
    response_model=WelcomeResponse,
    status_code=status.HTTP_200_OK,
    summary="API Welcome Information",
    description="Provides application metadata, version, and navigation links to documentation and the dashboard.",
)
def welcome_endpoint() -> WelcomeResponse:
    """Return an introductory welcome message for the Students Database CRUD API."""
    return WelcomeResponse(
        message="Welcome to the Students Database CRUD API (EWB Edu Tech Pvt. Ltd. Internship Assignment)",
        version=settings.VERSION,
        docs_url="/docs",
        dashboard_url="/dashboard",
    )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Validates that the FastAPI application and SQLite database connection are operational.",
)
def health_check_endpoint(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Check application and database health."""
    try:
        # Perform lightweight check query
        db.execute(text("SELECT 1"))
        return HealthCheckResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        ) from exc
