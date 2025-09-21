from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Import infrastructure
from .database import engine, get_db
from .infrastructure.database.models import Base
from .infrastructure.dependency_injection import container
from .config import OUTPUT_DIR

# Create app
app = FastAPI(
    title="Interactive Video Generator API",
    description="API for interactive video creation process (Hexagonal Architecture)",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add explicit OPTIONS handler for CORS preflight requests
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
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
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
app.mount("/api/videos", StaticFiles(directory=str(OUTPUT_DIR)), name="videos")

# Setup hexagonal architecture router
def get_project_router():
    """Create project router using dependency injection."""
    db = next(get_db())
    try:
        controller = container.get_project_controller(db)
        return controller.router
    finally:
        db.close()

# Include hexagonal architecture router
project_router = get_project_router()
app.include_router(
    project_router,
    prefix="/api/v1/projects",
    tags=["projects"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "architecture": "hexagonal"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
