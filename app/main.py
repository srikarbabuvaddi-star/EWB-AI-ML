"""Main application entry point for the Students Database CRUD Application."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import health, students

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("students_api")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists():
    alt_static = Path(__file__).resolve().parent.parent / "app" / "static"
    if alt_static.exists():
        STATIC_DIR = alt_static


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to initialize database schema on startup without wiping records."""
    logger.info("Starting up %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    try:
        init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.warning("Database schema initialization deferred: %s", exc)
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


# Global unhandled exception handler to ensure stack traces are never exposed
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


# Include API Routers
app.include_router(health.router)
app.include_router(students.router)

# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# User Interface Dashboard Route
@app.get(
    "/dashboard",
    include_in_schema=True,
    summary="Student Administration Dashboard",
    description="Interactive Web UI for managing student records.",
)
async def serve_dashboard():
    """Serve the single-page HTML administrative dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")

    # Fallback search for serverless packaging environments
    candidates = [
        Path("app/static/index.html"),
        Path("/var/task/app/static/index.html"),
        Path(__file__).resolve().parent.parent / "app" / "static" / "index.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return FileResponse(str(candidate), media_type="text/html")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Dashboard interface files not found."},
    )
