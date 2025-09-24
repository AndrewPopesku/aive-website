from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from projects.schemas import generate_id


# Render Task Schemas
class RenderTaskBase(BaseModel):
    """Base render task schema."""
    status: str = "pending"
    progress: int = 0


class RenderTaskCreate(RenderTaskBase):
    """Schema for creating a render task."""
    id: str = Field(default_factory=lambda: generate_id("task"))
    project_id: str
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None


class RenderTaskUpdate(BaseModel):
    """Schema for updating a render task."""
    status: Optional[str] = None
    progress: Optional[int] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None


class RenderTaskResponse(RenderTaskBase):
    """Schema for render task responses."""
    id: str
    project_id: str
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Render Request Schema
class RenderRequest(BaseModel):
    """Schema for video render requests."""
    add_subtitles: bool = True
    include_audio: bool = True


# Response Schemas
class RenderResponse(BaseModel):
    """Response schema for render requests."""
    render_task_id: str
    status_url: str


class RenderStatusResponse(BaseModel):
    """Response schema for render status queries."""
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[int] = None