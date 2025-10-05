import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import routers
from auth.routes import router as auth_router
from base.config import get_settings
from database.session import close_db, create_db_and_tables
from projects.routes import router as projects_router
from render.routes import router as render_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting up AIVE Backend API...")

    # Create database tables
    # await create_db_and_tables()
    # logger.info("Database tables created successfully")

    # Ensure directories exist
    settings.ensure_directories()
    logger.info("Required directories ensured")

    yield

    # Shutdown
    logger.info("Shutting down AIVE Backend API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="AIVE Backend API",
    description="Modern AI Video Editor Backend - Interactive video creation process",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
# Always use specific origins to support credentials (required for JWT auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,  # Required for JWT authentication with Authorization header
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
    expose_headers=["*"],
)


# Note: CORS preflight requests are handled automatically by CORSMiddleware


# Mount static files for videos
try:
    app.mount(
        "/api/videos", StaticFiles(directory=str(settings.output_dir)), name="videos"
    )
    logger.info(f"Mounted static files at /api/videos -> {settings.output_dir}")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Mount static files for audio/music
try:
    app.mount(
        "/api/audio", StaticFiles(directory=str(settings.audio_dir)), name="audio"
    )
    logger.info(f"Mounted static files at /api/audio -> {settings.audio_dir}")
except Exception as e:
    logger.warning(f"Could not mount audio static files: {e}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AIVE Backend API",
        "version": "0.1.0",
        "environment": settings.environment,
    }


# Register domain routers
def register_routes():
    """Register all domain routes with the FastAPI app."""

    # Authentication routes
    app.include_router(
        auth_router,
        prefix=f"{settings.api_prefix}/auth",
        tags=["Authentication"],
    )
    logger.info("Registered authentication routes")

    # Projects routes
    app.include_router(
        projects_router,
        prefix=f"{settings.api_prefix}/projects",
        tags=["Projects"],
    )
    logger.info("Registered projects routes")

    # Render routes
    app.include_router(
        render_router,
        prefix=f"{settings.api_prefix}/render",
        tags=["Render"],
    )
    logger.info("Registered render routes")


# Register all routes
register_routes()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.debug else str(exc),
            "type": "internal_server_error",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
