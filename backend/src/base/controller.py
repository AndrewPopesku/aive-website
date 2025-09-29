from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from base.repository import BaseRepository

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseController(Generic[RepositoryType]):
    """Base controller class with common business logic patterns."""

    def __init__(self, repository: RepositoryType):
        self.repository = repository

    async def create_entity(self, session: AsyncSession, data: Dict[str, Any]) -> Any:
        """Create a new entity with common validation and error handling."""
        try:
            return await self.repository.create(session, data)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create entity: {str(e)}")

    async def get_entity(self, session: AsyncSession, entity_id: Any) -> Any:
        """Get an entity with common error handling."""
        entity = await self.repository.get(session, entity_id)
        if not entity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity with ID {entity_id} not found")
        return entity

    async def get_entities(
        self, session: AsyncSession, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Get multiple entities with pagination and filtering."""
        try:
            return await self.repository.get_all(session, skip, limit, filters)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve entities: {str(e)}"
            )

    async def update_entity(self, session: AsyncSession, entity_id: Any, data: Dict[str, Any]) -> Any:
        """Update an entity with common validation and error handling."""
        try:
            # First check if entity exists
            await self.get_entity(session, entity_id)

            # Perform the update
            updated_entity = await self.repository.update(session, entity_id, data)
            if not updated_entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity with ID {entity_id} not found"
                )
            return updated_entity
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to update entity: {str(e)}")

    async def delete_entity(self, session: AsyncSession, entity_id: Any) -> bool:
        """Delete an entity with common validation and error handling."""
        try:
            # First check if entity exists
            await self.get_entity(session, entity_id)

            # Perform the deletion
            success = await self.repository.delete(session, entity_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity with ID {entity_id} not found"
                )
            return success
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete entity: {str(e)}"
            )

    async def validate_entity_exists(self, session: AsyncSession, entity_id: Any) -> None:
        """Validate that an entity exists, raise 404 if not found."""
        exists = await self.repository.exists(session, entity_id)
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity with ID {entity_id} not found")

    async def count_entities(self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        try:
            return await self.repository.count(session, filters)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to count entities: {str(e)}"
            )
