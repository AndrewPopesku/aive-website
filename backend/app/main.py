from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Import router and database
from app.routers import project
from app.database import engine
from app.models import Base
from app.config import OUTPUT_DIR

# Create app
app = FastAPI(
    title="Interactive Video Generator API",
    description="API for interactive video creation process",
    version="0.1.0"
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

# Include routers
app.include_router(
    project.router,
    prefix="/api/v1/projects",
    tags=["projects"],
)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)