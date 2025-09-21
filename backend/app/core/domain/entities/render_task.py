from typing import Optional
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
        """Mark the task as processing."""
        self.status = RenderStatus.PROCESSING
        self.progress = 0
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: int) -> None:
        """Update the progress of the render task."""
        self.progress = max(0, min(100, progress))  # Ensure progress is between 0-100
        self.updated_at = datetime.utcnow()
    
    def complete(self, output_file_path: str) -> None:
        """Mark the task as complete with output path."""
        self.status = RenderStatus.COMPLETE
        self.progress = 100
        self.output_file_path = output_file_path
        self.error_message = None
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        """Mark the task as failed with error message."""
        self.status = RenderStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def is_complete(self) -> bool:
        """Check if the task is complete."""
        return self.status == RenderStatus.COMPLETE
    
    def is_failed(self) -> bool:
        """Check if the task has failed."""
        return self.status == RenderStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if the task is currently being processed."""
        return self.status in [RenderStatus.PENDING, RenderStatus.PROCESSING]