from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(50), primary_key=True, index=True)  # Use string ID as primary key with length for full UUID
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Add description field
    audio_file_path = Column(String, nullable=True)  # Add audio file path field
    total_duration = Column(Float, nullable=True)
    overall_mood = Column(String, nullable=True)
    video_url = Column(String, nullable=True)  # Add video_url field to store the rendered video URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(String(50), primary_key=True, index=True)  # Changed from Integer to String for UUID
    project_id = Column(String(50), nullable=False)  # References Project.id
    text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)  # Store English translation for search
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    selected_footage = Column(JSON, nullable=True)  # Store selected footage as JSON

class FootageChoice(Base):
    __tablename__ = "footage_choices"

    id = Column(String(50), primary_key=True, index=True)  # Changed from Integer to String for UUID
    project_id = Column(String(50), nullable=False)
    sentence_id = Column(String(50), nullable=False)  # References Sentence.id, changed to String
    footage_options = Column(JSON, nullable=False)  # Store footage options as JSON

class MusicRecommendation(Base):
    __tablename__ = "music_recommendations"

    id = Column(String(50), primary_key=True, index=True)  # Changed from Integer to String for UUID
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

    id = Column(String(50), primary_key=True, index=True)  # Use string ID as primary key with length for full UUID
    project_id = Column(String(50), nullable=False)
    status = Column(String, default="pending")  # pending, processing, complete, failed
    progress = Column(Integer, default=0)
    output_file_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())