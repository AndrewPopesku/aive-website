from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Text, func
from sqlmodel import JSON, Column, Field, SQLModel


class Project(SQLModel, table=True):
    """Project model representing a video creation project."""

    __tablename__: str = "projects"

    id: str = Field(primary_key=True, max_length=50, index=True)
    title: str = Field(..., description="Project title")
    description: str | None = Field(None, sa_column=Column(Text))
    audio_file_path: str | None = Field(
        None, description="Path to the uploaded audio file"
    )
    total_duration: float | None = Field(None, description="Total duration in seconds")
    overall_mood: str | None = Field(None, description="Overall mood of the project")
    video_url: str | None = Field(None, description="URL to the rendered video")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        ),
    )


class Sentence(SQLModel, table=True):
    """Sentence model representing a transcribed sentence with timing."""

    __tablename__: str = "sentences"

    id: str = Field(primary_key=True, max_length=50, index=True)
    project_id: str = Field(..., max_length=50, foreign_key="projects.id", index=True)
    text: str = Field(..., sa_column=Column(Text))
    translated_text: str | None = Field(None, sa_column=Column(Text))
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    selected_footage: dict[str, Any] | None = Field(
        None, sa_column=Column(JSON), description="Selected footage information as JSON"
    )


class FootageChoice(SQLModel, table=True):
    """Footage choice model representing available footage options for sentences."""

    __tablename__: str = "footage_choices"

    id: str = Field(primary_key=True, max_length=50, index=True)
    project_id: str = Field(..., max_length=50, foreign_key="projects.id", index=True)
    sentence_id: str = Field(..., max_length=50, foreign_key="sentences.id", index=True)
    footage_options: dict[str, Any] = Field(
        ..., sa_column=Column(JSON), description="Available footage options as JSON"
    )


class MusicRecommendation(SQLModel, table=True):
    """Music recommendation model for project background music."""

    __tablename__: str = "music_recommendations"

    id: str = Field(primary_key=True, max_length=50, index=True)
    project_id: str = Field(..., max_length=50, foreign_key="projects.id", index=True)
    title: str = Field(..., description="Music track title")
    artist: str = Field(..., description="Artist name")
    genre: str | None = Field(None, description="Music genre")
    mood: str | None = Field(None, description="Music mood")
    energy_level: int | None = Field(None, description="Energy level (1-10)")
    url: str = Field(..., description="URL to the music file")
    duration: float | None = Field(None, description="Duration in seconds")
