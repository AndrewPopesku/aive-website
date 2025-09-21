from typing import List, Optional
from sqlalchemy.orm import Session

from ....core.domain.entities.sentence import Sentence as SentenceEntity
from ....core.domain.repositories.sentence_repository import SentenceRepository
from ....infrastructure.database.models import Sentence as SentenceModel


class DatabaseSentenceRepository(SentenceRepository):
    """Database implementation of SentenceRepository."""
    
    def __init__(self, db_session: Session):
        self._db = db_session
    
    async def create_many(self, sentences: List[SentenceEntity]) -> List[SentenceEntity]:
        """Create multiple sentences for a project."""
        db_sentences = []
        
        for sentence in sentences:
            db_sentence = SentenceModel(
                id=sentence.id,
                project_id=sentence.project_id,
                text=sentence.text,
                translated_text=sentence.translated_text,
                start_time=sentence.start_time,
                end_time=sentence.end_time,
                selected_footage=sentence.selected_footage
            )
            db_sentences.append(db_sentence)
            self._db.add(db_sentence)
        
        self._db.commit()
        
        for db_sentence in db_sentences:
            self._db.refresh(db_sentence)
        
        return [self._to_entity(db_sentence) for db_sentence in db_sentences]
    
    async def get_by_project_id(self, project_id: str) -> List[SentenceEntity]:
        """Get all sentences for a project."""
        db_sentences = self._db.query(SentenceModel).filter(
            SentenceModel.project_id == project_id
        ).all()
        
        return [self._to_entity(db_sentence) for db_sentence in db_sentences]
    
    async def get_by_id(self, sentence_id: str) -> Optional[SentenceEntity]:
        """Get a sentence by its ID."""
        db_sentence = self._db.query(SentenceModel).filter(
            SentenceModel.id == sentence_id
        ).first()
        
        if not db_sentence:
            return None
        
        return self._to_entity(db_sentence)
    
    async def update(self, sentence: SentenceEntity) -> SentenceEntity:
        """Update an existing sentence."""
        db_sentence = self._db.query(SentenceModel).filter(
            SentenceModel.id == sentence.id
        ).first()
        
        if not db_sentence:
            raise ValueError(f"Sentence {sentence.id} not found")
        
        # Update fields
        db_sentence.text = sentence.text
        db_sentence.translated_text = sentence.translated_text
        db_sentence.start_time = sentence.start_time
        db_sentence.end_time = sentence.end_time
        db_sentence.selected_footage = sentence.selected_footage
        
        self._db.commit()
        self._db.refresh(db_sentence)
        
        return self._to_entity(db_sentence)
    
    async def delete_by_project_id(self, project_id: str) -> bool:
        """Delete all sentences for a project."""
        deleted_count = self._db.query(SentenceModel).filter(
            SentenceModel.project_id == project_id
        ).delete()
        
        self._db.commit()
        return deleted_count > 0
    
    def _to_entity(self, db_sentence: SentenceModel) -> SentenceEntity:
        """Convert database model to domain entity."""
        return SentenceEntity(
            id=db_sentence.id,
            project_id=db_sentence.project_id,
            text=db_sentence.text or "",
            translated_text=db_sentence.translated_text,
            start_time=db_sentence.start_time or 0.0,
            end_time=db_sentence.end_time or 0.0,
            selected_footage=db_sentence.selected_footage
        )