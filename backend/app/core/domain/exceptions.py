"""Domain-specific exceptions for the video creator application.

This module contains custom exception classes that represent various error
conditions within the domain layer. These exceptions provide type-safe
error handling and better error messaging throughout the application.
"""

from __future__ import annotations

from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base exception for all domain-related errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.lower()
        self.details = details or {}
    
    def __str__(self) -> str:
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Repository Exceptions
class RepositoryError(DomainException):
    """Base exception for repository-related errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when a requested entity is not found."""
    
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with ID '{entity_id}' not found",
            "entity_not_found",
            {"entity_type": entity_type, "entity_id": entity_id}
        )


class EntityAlreadyExistsError(RepositoryError):
    """Raised when trying to create an entity that already exists."""
    
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with ID '{entity_id}' already exists",
            "entity_already_exists",
            {"entity_type": entity_type, "entity_id": entity_id}
        )


class RepositoryConnectionError(RepositoryError):
    """Raised when repository cannot connect to storage."""
    
    def __init__(self, storage_type: str, cause: Optional[str] = None) -> None:
        message = f"Cannot connect to {storage_type}"
        if cause:
            message += f": {cause}"
        super().__init__(message, "repository_connection_error")


# Service Exceptions
class ServiceError(DomainException):
    """Base exception for domain service errors."""
    pass


class TranscriptionError(ServiceError):
    """Raised when audio transcription fails."""
    
    def __init__(self, reason: str, audio_path: Optional[str] = None) -> None:
        super().__init__(
            f"Transcription failed: {reason}",
            "transcription_error",
            {"audio_path": audio_path} if audio_path else {}
        )


class TranslationError(ServiceError):
    """Raised when text translation fails."""
    
    def __init__(
        self, 
        reason: str, 
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> None:
        super().__init__(
            f"Translation failed: {reason}",
            "translation_error",
            {
                "source_language": source_lang,
                "target_language": target_lang
            }
        )


class FootageSearchError(ServiceError):
    """Raised when footage search fails."""
    
    def __init__(self, query: str, reason: str) -> None:
        super().__init__(
            f"Footage search failed for '{query}': {reason}",
            "footage_search_error",
            {"query": query}
        )


class VideoRenderingError(ServiceError):
    """Raised when video rendering fails."""
    
    def __init__(
        self, 
        reason: str, 
        project_id: Optional[str] = None,
        stage: Optional[str] = None
    ) -> None:
        super().__init__(
            f"Video rendering failed: {reason}",
            "video_rendering_error",
            {"project_id": project_id, "stage": stage}
        )


class MusicServiceError(ServiceError):
    """Raised when music service operations fail."""
    
    def __init__(self, reason: str, music_path: Optional[str] = None) -> None:
        super().__init__(
            f"Music service error: {reason}",
            "music_service_error",
            {"music_path": music_path} if music_path else {}
        )


# Validation Exceptions
class ValidationError(DomainException):
    """Raised when domain entity validation fails."""
    
    def __init__(
        self, 
        field: str, 
        value: Any, 
        constraint: str,
        entity_type: Optional[str] = None
    ) -> None:
        entity_part = f" in {entity_type}" if entity_type else ""
        super().__init__(
            f"Validation failed for field '{field}'{entity_part}: {constraint}",
            "validation_error",
            {
                "field": field,
                "value": str(value),
                "constraint": constraint,
                "entity_type": entity_type
            }
        )


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated."""
    
    def __init__(self, rule: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            f"Business rule violation: {rule}",
            "business_rule_violation",
            context or {}
        )


# Configuration Exceptions
class ConfigurationError(DomainException):
    """Raised when application configuration is invalid."""
    
    def __init__(self, setting: str, reason: str) -> None:
        super().__init__(
            f"Configuration error for '{setting}': {reason}",
            "configuration_error",
            {"setting": setting}
        )


# External Service Exceptions
class ExternalServiceError(DomainException):
    """Base exception for external service errors."""
    pass


class ExternalServiceUnavailableError(ExternalServiceError):
    """Raised when an external service is unavailable."""
    
    def __init__(self, service_name: str, status_code: Optional[int] = None) -> None:
        message = f"External service '{service_name}' is unavailable"
        if status_code:
            message += f" (status: {status_code})"
        super().__init__(
            message,
            "external_service_unavailable",
            {"service_name": service_name, "status_code": status_code}
        )


class ExternalServiceTimeoutError(ExternalServiceError):
    """Raised when an external service request times out."""
    
    def __init__(self, service_name: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Request to '{service_name}' timed out after {timeout_seconds}s",
            "external_service_timeout",
            {"service_name": service_name, "timeout_seconds": timeout_seconds}
        )


class RateLimitExceededError(ExternalServiceError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, service_name: str, retry_after: Optional[int] = None) -> None:
        message = f"Rate limit exceeded for '{service_name}'"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(
            message,
            "rate_limit_exceeded",
            {"service_name": service_name, "retry_after": retry_after}
        )