import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


def generate_id(prefix: str = "") -> str:
    """Generate unique IDs with optional prefix."""
    return f"{prefix}-{str(uuid.uuid4())}"


# Selected Footage Schema
class SelectedFootage(BaseModel):
    """Schema for selected footage information."""

    id: str
    title: str
    description: str
    thumbnail: str
    duration: float
    tags: List[str]
    category: str
    mood: str
    relevance_score: int
    url: str  # Changed from HttpUrl to str to avoid JSON serialization issues


# Project Schemas
class ProjectBase(BaseModel):
    """Base project schema."""

    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    id: str = Field(default_factory=lambda: generate_id("proj"))
    audio_file_path: str


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    title: Optional[str] = None
    description: Optional[str] = None
    total_duration: Optional[float] = None
    overall_mood: Optional[str] = None
    video_url: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses."""

    id: str
    audio_file_path: Optional[str] = None
    total_duration: Optional[float] = None
    overall_mood: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sentence Schemas
class SentenceBase(BaseModel):
    """Base sentence schema."""

    text: str
    translated_text: Optional[str] = None
    start_time: float
    end_time: float


class SentenceCreate(SentenceBase):
    """Schema for creating a sentence."""

    id: Optional[str] = Field(default_factory=lambda: generate_id("sent"))
    selected_footage: Optional[SelectedFootage] = None


class SentenceUpdate(BaseModel):
    """Schema for updating a sentence."""

    text: Optional[str] = None
    translated_text: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    selected_footage: Optional[SelectedFootage] = None


class SentenceResponse(SentenceBase):
    """Schema for sentence responses."""

    id: str
    project_id: str
    selected_footage: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Footage Choice Schemas
class FootageChoiceBase(BaseModel):
    """Base footage choice schema."""

    sentence_id: str


class FootageChoiceCreate(FootageChoiceBase):
    """Schema for creating footage choices."""

    id: Optional[str] = Field(default_factory=lambda: generate_id("foot"))
    footage_options: List[Dict[str, Any]]


class FootageChoiceResponse(FootageChoiceBase):
    """Schema for footage choice responses."""

    id: str
    project_id: str
    footage_options: List[Dict[str, Any]]

    class Config:
        from_attributes = True


# Music Recommendation Schemas
class MusicRecommendationBase(BaseModel):
    """Base music recommendation schema."""

    title: str
    artist: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    url: str
    duration: Optional[float] = None


class MusicRecommendationCreate(MusicRecommendationBase):
    """Schema for creating music recommendations."""

    id: Optional[str] = Field(default_factory=lambda: generate_id("music"))


class MusicRecommendationResponse(MusicRecommendationBase):
    """Schema for music recommendation responses."""

    id: str
    project_id: str

    class Config:
        from_attributes = True


# Legacy compatibility schemas
class Sentence(BaseModel):
    """Legacy sentence schema for backward compatibility."""

    sentence_id: str = Field(default_factory=lambda: generate_id("sent"))
    text: str
    translated_text: Optional[str] = None
    start: float
    end: float
    recommended_footage_url: Optional[str] = None
    selected_footage: Optional[SelectedFootage] = None


class FootageChoice(BaseModel):
    """Legacy footage choice schema."""

    sentence_id: str
    footage_url: str


class FootageChoices(BaseModel):
    """Legacy footage choices collection."""

    footage_choices: List[FootageChoice]


class MusicRecommendation(BaseModel):
    """Legacy music recommendation schema."""

    id: str
    name: str
    url: str


# Response Schemas
class ProjectResponseLegacy(BaseModel):
    """Legacy project response schema."""

    project_id: str
    sentences: List[Sentence]


class MusicResponse(BaseModel):
    """Music recommendation response."""

    project_id: str
    recommended_music: List[MusicRecommendation]
