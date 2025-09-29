from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Text, func
from sqlmodel import Column, Field, SQLModel


class RenderTask(SQLModel, table=True):
    """Render task model representing video rendering operations."""

    __tablename__ = "render_tasks"

    id: str = Field(primary_key=True, max_length=50, index=True)
    project_id: str = Field(..., max_length=50, foreign_key="projects.id", index=True)
    status: str = Field(default="pending", description="Task status: pending, processing, complete, failed")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    output_file_path: Optional[str] = Field(None, description="Path to the rendered video file")
    error_message: Optional[str] = Field(None, sa_column=Column(Text), description="Error message if task failed")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
