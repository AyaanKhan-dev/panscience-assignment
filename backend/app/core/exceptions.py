"""Custom exception classes for the application."""
from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class FileNotFoundError(AppException):
    """File not found exception."""

    def __init__(self, file_id: str):
        super().__init__(
            message=f"File with ID {file_id} not found",
            status_code=404
        )


class FileProcessingError(AppException):
    """File processing exception."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details
        )


class UnsupportedFileTypeError(AppException):
    """Unsupported file type exception."""

    def __init__(self, file_type: str):
        super().__init__(
            message=f"File type '{file_type}' is not supported",
            status_code=415
        )


class TranscriptionError(AppException):
    """Transcription service exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Transcription failed: {message}",
            status_code=500
        )


class EmbeddingError(AppException):
    """Embedding generation exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Embedding generation failed: {message}",
            status_code=500
        )


class LLMError(AppException):
    """LLM service exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"LLM service error: {message}",
            status_code=500
        )


class RateLimitError(AppException):
    """Rate limit exceeded exception."""

    def __init__(self):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=429
        )
