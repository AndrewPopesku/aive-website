from typing import List, Optional
from sqlalchemy.orm import Session

from ....core.domain.entities.music import MusicRecommendation as MusicEntity
from ....core.domain.repositories.music_repository import MusicRepository
from ....infrastructure.database.models import MusicRecommendation as MusicModel


class DatabaseMusicRepository(MusicRepository):
    """Database implementation of MusicRepository."""
    
    def __init__(self, db_session: Session):
        self._db = db_session
    
    async def create_many(self, music_recs: List[MusicEntity]) -> List[MusicEntity]:
        """Create multiple music recommendations for a project."""
        db_music_recs = []
        
        for music in music_recs:
            db_music = MusicModel(
                id=music.id,
                project_id=music.project_id,
                title=music.title,
                artist=music.artist,
                genre=music.genre,
                mood=music.mood,
                energy_level=music.energy_level,
                url=music.url,
                duration=music.duration
            )
            db_music_recs.append(db_music)
            self._db.add(db_music)
        
        self._db.commit()
        
        for db_music in db_music_recs:
            self._db.refresh(db_music)
        
        return [self._to_entity(db_music) for db_music in db_music_recs]
    
    async def get_by_project_id(self, project_id: str) -> List[MusicEntity]:
        """Get all music recommendations for a project."""
        db_music_recs = self._db.query(MusicModel).filter(
            MusicModel.project_id == project_id
        ).all()
        
        return [self._to_entity(db_music) for db_music in db_music_recs]
    
    async def get_by_id(self, music_id: str) -> Optional[MusicEntity]:
        """Get a music recommendation by its ID."""
        db_music = self._db.query(MusicModel).filter(
            MusicModel.id == music_id
        ).first()
        
        if not db_music:
            return None
        
        return self._to_entity(db_music)
    
    async def delete_by_project_id(self, project_id: str) -> bool:
        """Delete all music recommendations for a project."""
        deleted_count = self._db.query(MusicModel).filter(
            MusicModel.project_id == project_id
        ).delete()
        
        self._db.commit()
        return deleted_count > 0
    
    def _to_entity(self, db_music: MusicModel) -> MusicEntity:
        """Convert database model to domain entity."""
        return MusicEntity(
            id=db_music.id,
            project_id=db_music.project_id,
            title=db_music.title or "",
            artist=db_music.artist or "",
            genre=db_music.genre,
            mood=db_music.mood,
            energy_level=db_music.energy_level,
            url=db_music.url or "",
            duration=db_music.duration
        )