from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from sqlmodel import SQLModel, select, Session
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def create(self, session: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new object in the database."""
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get an object by ID."""
        statement = select(self.model).where(self.model.id == id)
        result = await session.exec(statement)
        return result.first()
    
    async def get_all(
        self, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get all objects with optional filtering and pagination."""
        statement = select(self.model)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    statement = statement.where(getattr(self.model, key) == value)
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        
        result = await session.exec(statement)
        return result.all()
    
    async def update(
        self, 
        session: AsyncSession, 
        id: Any, 
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an object by ID."""
        db_obj = await self.get(session, id)
        if not db_obj:
            return None
        
        for key, value in obj_in.items():
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
        self, 
        session: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count objects with optional filtering."""
        from sqlalchemy import func
        
        statement = select(func.count(self.model.id))
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    statement = statement.where(getattr(self.model, key) == value)
        
        result = await session.exec(statement)
        return result.one()