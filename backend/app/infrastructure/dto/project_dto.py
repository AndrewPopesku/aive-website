from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FootageChoiceDTO(BaseModel):
    """DTO for footage choice."""
    sentence_id: str
    footage_url: str


class FootageChoicesDTO(BaseModel):
    """DTO for multiple footage choices."""
    footage_choices: List[FootageChoiceDTO]


class RenderRequestDTO(BaseModel):
    """DTO for render request."""
    add_subtitles: bool = True
    include_audio: bool = True


class RenderResponseDTO(BaseModel):
    """DTO for render response."""
    render_task_id: str
    status_url: str


class RenderStatusResponseDTO(BaseModel):
    """DTO for render status response."""
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None


class ProjectResponseDTO(BaseModel):
    """DTO for project response."""
    project_id: str
    sentences: List[Dict[str, Any]]


class MusicResponseDTO(BaseModel):
    """DTO for music response."""
    project_id: str
    recommended_music: List[Dict[str, Any]]