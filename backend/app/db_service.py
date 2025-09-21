from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import uuid

from app.models import Project, Sentence, FootageChoice, MusicRecommendation, RenderTask
from app.schemas import (
    ProjectCreate, ProjectResponse, SentenceCreate, SentenceResponse,
    FootageChoiceCreate, FootageChoiceResponse, MusicRecommendationCreate,
    MusicRecommendationResponse, RenderTaskCreate, RenderTaskResponse,
    SelectedFootage, generate_id
)


# Project CRUD operations
def create_project(db: Session, project: ProjectCreate) -> Project:
    """Create a new project in the database."""
    db_project = Project(
        id=project.id,
        title=project.title,
        description=project.description,
        audio_file_path=project.audio_file_path,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    return db.query(Project).filter(Project.id == project_id).first()


def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """List all projects with pagination."""
    return db.query(Project).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: str, project_update: Dict[str, Any]) -> Optional[Project]:
    """Update a project."""
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    for key, value in project_update.items():
        if hasattr(db_project, key):
            setattr(db_project, key, value)
    
    db_project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: str) -> bool:
    """Delete a project and all related data."""
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True


# Sentence CRUD operations
def create_sentences(db: Session, project_id: str, sentences: List[SentenceCreate]) -> List[Sentence]:
    """Create sentences for a project."""
    db_sentences = []
    for sentence_data in sentences:
        # Convert selected_footage to JSON if it exists
        selected_footage_json = None
        if sentence_data.selected_footage:
            # Convert to dict and ensure HttpUrl objects are serialized as strings
            selected_footage_dict = sentence_data.selected_footage.model_dump()
            # Convert HttpUrl to string for JSON serialization
            if 'url' in selected_footage_dict:
                selected_footage_dict['url'] = str(selected_footage_dict['url'])
            selected_footage_json = selected_footage_dict
        
        # Use provided ID or generate a new one
        sentence_id = sentence_data.id if hasattr(sentence_data, "id") and sentence_data.id else generate_id("sent")
        
        db_sentence = Sentence(
            id=sentence_id,
            project_id=project_id,
            text=sentence_data.text,
            translated_text=sentence_data.translated_text,
            start_time=sentence_data.start_time,
            end_time=sentence_data.end_time,
            selected_footage=selected_footage_json
        )
        db_sentences.append(db_sentence)
        db.add(db_sentence)
    
    db.commit()
    for sentence in db_sentences:
        db.refresh(sentence)
    
    return db_sentences


def get_sentences(db: Session, project_id: str) -> List[Sentence]:
    """Get all sentences for a project."""
    return db.query(Sentence).filter(Sentence.project_id == project_id).all()


def update_sentence_footage(db: Session, sentence_id: str, selected_footage: SelectedFootage) -> Optional[Sentence]:
    """Update selected footage for a sentence."""
    db_sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    if not db_sentence:
        return None
    
    # Convert to dict and ensure HttpUrl objects are serialized as strings
    selected_footage_dict = selected_footage.model_dump()
    if 'url' in selected_footage_dict:
        selected_footage_dict['url'] = str(selected_footage_dict['url'])
    
    db_sentence.selected_footage = selected_footage_dict
    db.commit()
    db.refresh(db_sentence)
    return db_sentence


# Footage Choice CRUD operations
def create_footage_choices(db: Session, project_id: str, footage_choices: List[Any]) -> List[FootageChoice]:
    """Create footage choices for a project."""
    db_footage_choices = []
    for choice_data in footage_choices:
        # Handle both dictionary input and FootageChoice object
        sentence_id = None
        footage_options = []
        
        # Extract sentence_id and footage_url
        if isinstance(choice_data, dict):
            # Dictionary input
            if 'sentence_id' in choice_data:
                sentence_id = choice_data['sentence_id']
            
            # Add footage_url as an option if it exists
            if 'footage_url' in choice_data:
                footage_options = [{'url': str(choice_data['footage_url'])}]
        else:
            # Handle FootageChoice object (from schemas.py)
            sentence_id = choice_data.sentence_id
            
            # If it has footage_url attribute, use it
            if hasattr(choice_data, 'footage_url'):
                footage_url = str(choice_data.footage_url)
                footage_options = [{'url': footage_url}]
            # If it has footage_options attribute, use it
            elif hasattr(choice_data, 'footage_options'):
                footage_options = choice_data.footage_options
        
        # Generate a new ID for the footage choice
        footage_id = generate_id("foot")
        
        db_choice = FootageChoice(
            id=footage_id,
            project_id=project_id,
            sentence_id=sentence_id,
            footage_options=footage_options
        )
        db_footage_choices.append(db_choice)
        db.add(db_choice)
    
    db.commit()
    for choice in db_footage_choices:
        db.refresh(choice)
    
    return db_footage_choices


def get_footage_choices(db: Session, project_id: str) -> List[FootageChoice]:
    """Get all footage choices for a project."""
    return db.query(FootageChoice).filter(FootageChoice.project_id == project_id).all()


def get_footage_choices_by_sentence(db: Session, sentence_id: str) -> Optional[FootageChoice]:
    """Get footage choices for a specific sentence."""
    return db.query(FootageChoice).filter(FootageChoice.sentence_id == sentence_id).first()


# Music Recommendation CRUD operations
def create_music_recommendations(db: Session, project_id: str, music_recs: List[MusicRecommendationCreate]) -> List[MusicRecommendation]:
    """Create music recommendations for a project."""
    db_music_recs = []
    for rec_data in music_recs:
        # Generate ID if not provided
        music_id = rec_data.id if hasattr(rec_data, "id") and rec_data.id else generate_id("music")
        
        db_rec = MusicRecommendation(
            id=music_id,
            project_id=project_id,
            title=rec_data.title,
            artist=rec_data.artist,
            genre=rec_data.genre,
            mood=rec_data.mood,
            energy_level=rec_data.energy_level,
            url=rec_data.url,
            duration=rec_data.duration
        )
        db_music_recs.append(db_rec)
        db.add(db_rec)
    
    db.commit()
    for rec in db_music_recs:
        db.refresh(rec)
    
    return db_music_recs


def get_music_recommendations(db: Session, project_id: str) -> List[MusicRecommendation]:
    """Get all music recommendations for a project."""
    return db.query(MusicRecommendation).filter(MusicRecommendation.project_id == project_id).all()


# Render Task CRUD operations
def create_render_task(db: Session, task_data: RenderTaskCreate) -> RenderTask:
    """Create a new render task."""
    db_task = RenderTask(
        id=task_data.id,
        project_id=task_data.project_id,
        status=task_data.status,
        progress=task_data.progress,
        output_file_path=task_data.output_file_path,
        error_message=task_data.error_message
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_render_task(db: Session, task_id: str) -> Optional[RenderTask]:
    """Get a render task by ID."""
    return db.query(RenderTask).filter(RenderTask.id == task_id).first()


def update_render_task(db: Session, task_id: str, task_update: Dict[str, Any]) -> Optional[RenderTask]:
    """Update a render task."""
    db_task = get_render_task(db, task_id)
    if not db_task:
        return None
    
    for key, value in task_update.items():
        if hasattr(db_task, key):
            setattr(db_task, key, value)
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


def update_render_task_status(db: Session, task_id: str, status: str, video_url: str = None, progress: int = None, error_message: str = None) -> Optional[RenderTask]:
    """Update the status of a render task."""
    db_task = get_render_task(db, task_id)
    if not db_task:
        return None
    
    db_task.status = status
    if progress is not None:
        db_task.progress = progress
    if video_url:
        db_task.output_file_path = video_url
    if error_message:
        db_task.error_message = error_message
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


# Utility functions
def validate_project_exists(db: Session, project_id: str) -> bool:
    """Check if a project exists."""
    return db.query(Project).filter(Project.id == project_id).first() is not None


def get_project_with_all_data(db: Session, project_id: str) -> Optional[Dict[str, Any]]:
    """Get a project with all related data."""
    project = get_project(db, project_id)
    if not project:
        return None
    
    sentences = get_sentences(db, project_id)
    footage_choices = get_footage_choices(db, project_id)
    music_recommendations = get_music_recommendations(db, project_id)
    
    result = db_project_to_dict(project)
    result["sentences"] = [db_sentence_to_schema(s) for s in sentences]
    result["footage_choices"] = [f.footage_options for f in footage_choices]
    result["music_recommendations"] = [
        {"id": m.id, "title": m.title, "artist": m.artist, "url": m.url} for m in music_recommendations
    ]
    
    return result


def db_sentence_to_schema(db_sentence: Sentence) -> SentenceResponse:
    """Convert a Sentence model to a SentenceResponse schema."""
    return SentenceResponse(
        id=db_sentence.id,
        project_id=db_sentence.project_id,
        text=db_sentence.text,
        translated_text=db_sentence.translated_text,
        start_time=db_sentence.start_time,
        end_time=db_sentence.end_time,
        selected_footage=db_sentence.selected_footage
    )


def db_project_to_dict(db_project: Project, sentences: List[Sentence] = None, video_url: str = None) -> Dict[str, Any]:
    """Convert a Project model to a dictionary."""
    result = {
        "id": db_project.id,
        "project_id": db_project.id,
        "title": db_project.title or f"Project {db_project.id}",
        "description": db_project.description,
        "audio_file_path": db_project.audio_file_path,  # Include audio file path
        "created_at": db_project.created_at.isoformat(),
        "updated_at": db_project.updated_at.isoformat(),
        "total_duration": db_project.total_duration,
        "overall_mood": db_project.overall_mood,
        "videoUrl": video_url or db_project.video_url
    }
    
    if sentences:
        result["sentences"] = [db_sentence_to_schema(s) for s in sentences]
        result["total_sentences"] = len(sentences)
        result["total_duration"] = sum(s.end_time - s.start_time for s in sentences)
    
    return result