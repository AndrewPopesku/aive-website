import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from src.base.config import get_settings
from src.database.session import create_db_and_tables, close_db

# Import routers
from src.projects.routes import router as projects_router
from src.render.routes import router as render_router

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
    await create_db_and_tables()
    logger.info("Database tables created successfully")
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add explicit OPTIONS handler for CORS preflight requests
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight requests."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


# Mount static files for videos
try:
    app.mount(
        "/api/videos", 
        StaticFiles(directory=str(settings.output_dir)), 
        name="videos"
    )
    logger.info(f"Mounted static files at /api/videos -> {settings.output_dir}")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Mount static files for audio/music
try:
    app.mount(
        "/api/audio", 
        StaticFiles(directory=str(settings.audio_dir)), 
        name="audio"
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
        "environment": settings.environment
    }


# Register domain routers
def register_routes():
    """Register all domain routes with the FastAPI app."""
    
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
            "type": "internal_server_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
