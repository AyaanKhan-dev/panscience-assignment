"""Pydantic schemas for media endpoints."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class MediaFileCreate(BaseModel):
    """Schema for media file creation (used internally)."""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    media_type: str


class MediaFileResponse(BaseModel):
    """Schema for media file response."""
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    media_type: str
    duration: Optional[float] = None
    status: str
    summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TranscriptSegmentResponse(BaseModel):
    """Schema for transcript segment response."""
    id: UUID
    text: str
    start_time: float
    end_time: float

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    """Schema for transcript response."""
    id: UUID
    media_file_id: UUID
    full_text: Optional[str] = None
    segments: List[TranscriptSegmentResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class TimestampQueryRequest(BaseModel):
    """Schema for timestamp query request."""
    query: str


class TimestampResult(BaseModel):
    """Schema for a single timestamp result."""
    text: str
    start_time: float
    end_time: float
    relevance_score: float


class TimestampQueryResponse(BaseModel):
    """Schema for timestamp query response."""
    query: str
    results: List[TimestampResult]
    answer: str
