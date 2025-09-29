from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from base.controller import BaseController

ControllerType = TypeVar("ControllerType", bound=BaseController)


class BaseAPISet(Generic[ControllerType], ABC):  # noqa: UP046
    """Base API set class for consistent route registration."""

    def __init__(
        self, prefix: str, controller: ControllerType, tags: list | None = None
    ):
        self.router = APIRouter()
        self.prefix = prefix
        self.controller = controller
        self.tags = tags or []
        self._register_routes()

    @abstractmethod
    def _register_routes(self):
        """Register all routes for this API set."""
        pass

    def _setup_crud_routes(self, get_session_dependency):
        """Standard CRUD route setup that can be reused."""

        @self.router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_entity(
            data: dict, session: AsyncSession = Depends(get_session_dependency)
        ):
            """Create a new entity."""
            return await self.controller.create_entity(session, data)

        @self.router.get("/{entity_id}")
        async def get_entity(
            entity_id: str, session: AsyncSession = Depends(get_session_dependency)
        ):
            """Get an entity by ID."""
            return await self.controller.get_entity(session, entity_id)

        @self.router.get("/")
        async def get_entities(
            skip: int = 0,
            limit: int = 100,
            session: AsyncSession = Depends(get_session_dependency),
        ):
            """Get multiple entities with pagination."""
            return await self.controller.get_entities(session, skip, limit)

        @self.router.put("/{entity_id}")
        async def update_entity(
            entity_id: str,
            data: dict,
            session: AsyncSession = Depends(get_session_dependency),
        ):
            """Update an entity by ID."""
            return await self.controller.update_entity(session, entity_id, data)

        @self.router.patch("/{entity_id}")
        async def patch_entity(
            entity_id: str,
            data: dict,
            session: AsyncSession = Depends(get_session_dependency),
        ):
            """Partially update an entity by ID."""
            return await self.controller.update_entity(session, entity_id, data)

        @self.router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_entity(
            entity_id: str, session: AsyncSession = Depends(get_session_dependency)
        ):
            """Delete an entity by ID."""
            await self.controller.delete_entity(session, entity_id)
            return None


class CRUDAPISet(BaseAPISet[ControllerType]):
    """A complete CRUD API set with standard operations."""

    def __init__(
        self,
        prefix: str,
        controller: ControllerType,
        get_session_dependency,
        tags: list | None = None,
    ):
        self.get_session_dependency = get_session_dependency
        super().__init__(prefix, controller, tags)

    def _register_routes(self):
        """Register standard CRUD routes."""
        self._setup_crud_routes(self.get_session_dependency)
