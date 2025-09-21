from __future__ import annotations

from typing import Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


class RenderStatus(Enum):
    """Possible render task statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    
    def __str__(self) -> str:
        """Return the string value of the status."""
        return self.value


# Type alias for literal render status values
RenderStatusLiteral = Literal["pending", "processing", "complete", "failed"]


@dataclass
class RenderTask:
    """Render task domain entity."""
    
    id: str = field(default_factory=lambda: f"task-{str(uuid.uuid4())}")
    project_id: str = ""
    status: RenderStatus = RenderStatus.PENDING
    progress: int = 0
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def start_processing(self) -> None:
        """Mark the task as processing.
        
        Raises:
            RuntimeError: If task is already complete or failed
        """
        if self.status in [RenderStatus.COMPLETE, RenderStatus.FAILED]:
            raise RuntimeError(f"Cannot start processing task in {self.status.value} state")
            
        self.status = RenderStatus.PROCESSING
        self.progress = 0
        self.error_message = None  # Clear any previous errors
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: int) -> None:
        """Update the progress of the render task.
        
        Args:
            progress: Progress percentage (0-100)
            
        Raises:
            ValueError: If progress is not between 0 and 100
            RuntimeError: If task is not in processing state
        """
        if not (0 <= progress <= 100):
            raise ValueError(f"Progress must be between 0 and 100, got {progress}")
            
        if self.status != RenderStatus.PROCESSING:
            raise RuntimeError(f"Cannot update progress for task in {self.status.value} state")
            
        self.progress = progress
        self.updated_at = datetime.utcnow()
    
    def complete(self, output_file_path: str) -> None:
        """Mark the task as complete with output path.
        
        Args:
            output_file_path: Path to the rendered output file
            
        Raises:
            ValueError: If output_file_path is empty
            RuntimeError: If task is already complete
        """
        if not output_file_path.strip():
            raise ValueError("Output file path cannot be empty")
            
        if self.status == RenderStatus.COMPLETE:
            raise RuntimeError("Task is already complete")
            
        self.status = RenderStatus.COMPLETE
        self.progress = 100
        self.output_file_path = output_file_path.strip()
        self.error_message = None
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        """Mark the task as failed with error message.
        
        Args:
            error_message: Descriptive error message
            
        Raises:
            ValueError: If error_message is empty
        """
        if not error_message.strip():
            raise ValueError("Error message cannot be empty")
            
        self.status = RenderStatus.FAILED
        self.error_message = error_message.strip()
        self.updated_at = datetime.utcnow()
    
    def is_complete(self) -> bool:
        """Check if the task is complete.
        
        Returns:
            True if task status is COMPLETE, False otherwise
        """
        return self.status == RenderStatus.COMPLETE
    
    def is_failed(self) -> bool:
        """Check if the task has failed.
        
        Returns:
            True if task status is FAILED, False otherwise
        """
        return self.status == RenderStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if the task is currently being processed.
        
        Returns:
            True if task is PENDING or PROCESSING, False otherwise
        """
        return self.status in [RenderStatus.PENDING, RenderStatus.PROCESSING]
    
    def get_status_display(self) -> str:
        """Get a human-readable status display.
        
        Returns:
            Formatted status string with progress if applicable
        """
        if self.status == RenderStatus.PROCESSING:
            return f"Processing ({self.progress}%)"
        return self.status.value.title()
