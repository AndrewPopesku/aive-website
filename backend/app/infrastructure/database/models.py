from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class RenderStatusEnum(enum.Enum):
    """Enum for render task statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    audio_file_path = Column(String, nullable=True)
    total_duration = Column(Float, nullable=True)
    overall_mood = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    selected_footage = Column(JSON, nullable=True)


class MusicRecommendation(Base):
    __tablename__ = "music_recommendations"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), nullable=False)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    mood = Column(String, nullable=True)
    energy_level = Column(Integer, nullable=True)
    url = Column(String, nullable=False)
    duration = Column(Float, nullable=True)


class RenderTask(Base):
    __tablename__ = "render_tasks"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), nullable=False)
    status = Column(Enum(RenderStatusEnum), default=RenderStatusEnum.PENDING)
    progress = Column(Integer, default=0)
    output_file_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())