from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Helper function to generate unique IDs
def generate_id(prefix: str = "") -> str:
    return f"{prefix}-{str(uuid.uuid4())}"

# Model for Selected Footage
class SelectedFootage(BaseModel):
    id: str
    title: str
    description: str
    thumbnail: str
    duration: float
    tags: List[str]
    category: str
    mood: str
    relevance_score: int
    url: HttpUrl

# Base schemas for database operations
class ProjectCreate(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("proj"))
    title: str
    description: Optional[str] = None
    audio_file_path: str

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    audio_file_path: str
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SentenceCreate(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: generate_id("sent"))
    text: str
    translated_text: Optional[str] = None  # Store English translation for search
    start_time: float
    end_time: float
    selected_footage: Optional[SelectedFootage] = None

class SentenceResponse(BaseModel):
    id: str
    project_id: str
    text: str
    translated_text: Optional[str] = None  # Store English translation for search
    start_time: float
    end_time: float
    selected_footage: Optional[Dict[str, Any]] = None

class FootageChoiceCreate(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: generate_id("foot"))
    sentence_id: str
    footage_options: List[Dict[str, Any]]

class FootageChoiceResponse(BaseModel):
    id: str
    project_id: str
    sentence_id: str
    footage_options: List[Dict[str, Any]]

class MusicRecommendationCreate(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: generate_id("music"))
    title: str
    artist: str
    genre: str
    mood: str
    energy_level: int
    url: str
    duration: float

class MusicRecommendationResponse(BaseModel):
    id: str
    project_id: str
    title: str
    artist: str
    genre: str
    mood: str
    energy_level: int
    url: str
    duration: float

class RenderTaskCreate(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("task"))
    project_id: str
    status: str = "pending"
    progress: int = 0
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None

class RenderTaskResponse(BaseModel):
    id: str
    project_id: str
    status: str
    progress: int
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Models for Sentence and Footage (legacy compatibility)
class Sentence(BaseModel):
    sentence_id: str = Field(default_factory=lambda: generate_id("sent"))
    text: str
    translated_text: Optional[str] = None  # Store English translation for search
    start: float
    end: float
    recommended_footage_url: Optional[HttpUrl] = None
    selected_footage: Optional[SelectedFootage] = None

class FootageChoice(BaseModel):
    sentence_id: str
    footage_url: HttpUrl

class FootageChoices(BaseModel):
    footage_choices: List[FootageChoice]

# Models for Music (legacy compatibility)
class MusicRecommendation(BaseModel):
    id: str
    name: str
    url: str

# Models for Render (legacy compatibility)
class RenderRequest(BaseModel):
    add_subtitles: bool = True
    include_audio: bool = True

# Response models (legacy compatibility)
class ProjectResponse(BaseModel):
    project_id: str
    sentences: List[Sentence]

class MusicResponse(BaseModel):
    project_id: str
    recommended_music: List[MusicRecommendation]

class RenderResponse(BaseModel):
    render_task_id: str
    status_url: str

class RenderStatusResponse(BaseModel):
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None