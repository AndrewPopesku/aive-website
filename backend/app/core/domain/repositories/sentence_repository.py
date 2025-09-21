from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.sentence import Sentence


class SentenceRepository(ABC):
    """Abstract repository for Sentence entities."""
    
    @abstractmethod
    async def create_many(self, sentences: List[Sentence]) -> List[Sentence]:
        """Create multiple sentences for a project."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List[Sentence]:
        """Get all sentences for a project."""
        pass
    
    @abstractmethod
    async def get_by_id(self, sentence_id: str) -> Optional[Sentence]:
        """Get a sentence by its ID."""
        pass
    
    @abstractmethod
    async def update(self, sentence: Sentence) -> Sentence:
        """Update an existing sentence."""
        pass
    
    @abstractmethod
    async def delete_by_project_id(self, project_id: str) -> bool:
        """Delete all sentences for a project."""
        pass