"""Common Pydantic schemas."""
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel


class StatusResponse(BaseModel):
    """Schema for status check response."""
    id: UUID
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[Any] = None
    status_code: int


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    redis: str


class UploadResponse(BaseModel):
    """Schema for file upload response."""
    id: UUID
    filename: str
    file_type: str
    status: str
    message: str
