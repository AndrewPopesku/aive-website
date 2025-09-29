from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository[ModelType: SQLModel]:
    """Base repository class with common CRUD operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def create(self, session: AsyncSession, obj_in: dict[str, Any]) -> ModelType:
        """Create a new object in the database."""
        # Convert HttpUrl objects to strings for JSON serialization
        processed_obj_in = self._process_httourls(obj_in)
        db_obj = self.model(**processed_obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get(self, session: AsyncSession, id: Any) -> ModelType | None:
        """Get an object by ID."""
        statement = select(self.model).where(self.model.id == id)  # type: ignore
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """Get all objects with optional filtering and pagination."""
        statement = select(self.model)

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    statement = statement.where(getattr(self.model, key) == value)

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, id: Any, obj_in: dict[str, Any]
    ) -> ModelType | None:
        """Update an object by ID."""
        db_obj = await self.get(session, id)
        if not db_obj:
            return None

        # Convert HttpUrl objects to strings for JSON serialization
        processed_obj_in = self._process_httourls(obj_in)

        for key, value in processed_obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Delete an object by ID."""
        db_obj = await self.get(session, id)
        if not db_obj:
            return False

        await session.delete(db_obj)
        await session.commit()
        return True

    async def exists(self, session: AsyncSession, id: Any) -> bool:
        """Check if an object exists by ID."""
        db_obj = await self.get(session, id)
        return db_obj is not None

    async def count(
        self, session: AsyncSession, filters: dict[str, Any] | None = None
    ) -> int:
        """Count objects with optional filtering."""
        from sqlalchemy import func

        statement = select(func.count(self.model.id))  # type: ignore

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    statement = statement.where(getattr(self.model, key) == value)

        result = await session.execute(statement)
        return result.scalar_one()

    def _process_httourls(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively convert HttpUrl objects to strings for JSON serialization."""
        from pydantic import HttpUrl

        processed_data = {}
        for key, value in data.items():
            if isinstance(value, HttpUrl):
                processed_data[key] = str(value)
            elif isinstance(value, dict):
                processed_data[key] = self._process_httourls(value)
            elif isinstance(value, list):
                processed_data[key] = [
                    (
                        self._process_httourls(item)
                        if isinstance(item, dict)
                        else (
                            str(item)
                            if hasattr(item, "__class__")
                            and item.__class__.__name__ == "HttpUrl"
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                processed_data[key] = value
        return processed_data
