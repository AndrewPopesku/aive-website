from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from ..entities.project import Project


class ProjectRepository(ABC):
    """Abstract repository for Project entities.
    
    This repository interface defines the contract for persisting and retrieving
    Project domain entities. Implementations should handle data persistence concerns
    while maintaining domain object integrity.
    """
    
    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project in the repository.
        
        Args:
            project: The Project entity to create
            
        Returns:
            The created Project entity with any generated fields populated
            
        Raises:
            ValueError: If project data is invalid
            RepositoryError: If creation fails due to storage issues
        """
        ...
    
    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by its unique identifier.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            The Project entity if found, None otherwise
            
        Raises:
            ValueError: If project_id is empty or invalid
            RepositoryError: If retrieval fails due to storage issues
        """
        ...
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Retrieve all projects with pagination support.
        
        Args:
            skip: Number of projects to skip (for pagination)
            limit: Maximum number of projects to return
            
        Returns:
            List of Project entities, may be empty
            
        Raises:
            ValueError: If skip < 0 or limit <= 0 or limit > 1000
            RepositoryError: If retrieval fails due to storage issues
        """
        if skip < 0:
            raise ValueError("Skip must be non-negative")
        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        ...
    
    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update an existing project in the repository.
        
        Args:
            project: The Project entity with updated data
            
        Returns:
            The updated Project entity
            
        Raises:
            ValueError: If project data is invalid
            NotFoundError: If project doesn't exist
            RepositoryError: If update fails due to storage issues
        """
        ...
    
    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """Delete a project by its unique identifier.
        
        Args:
            project_id: The unique identifier of the project to delete
            
        Returns:
            True if project was deleted, False if it didn't exist
            
        Raises:
            ValueError: If project_id is empty or invalid
            RepositoryError: If deletion fails due to storage issues
        """
        if not project_id.strip():
            raise ValueError("Project ID cannot be empty")
        ...
    
    @abstractmethod
    async def exists(self, project_id: str) -> bool:
        """Check if a project exists in the repository.
        
        Args:
            project_id: The unique identifier of the project
            
        Returns:
            True if project exists, False otherwise
            
        Raises:
            ValueError: If project_id is empty or invalid
            RepositoryError: If check fails due to storage issues
        """
        if not project_id.strip():
            raise ValueError("Project ID cannot be empty")
        ...
