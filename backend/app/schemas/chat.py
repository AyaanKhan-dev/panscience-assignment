"""Pydantic schemas for chat endpoints."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    source_type: Optional[str] = None  # 'document' or 'media'


class TimestampReference(BaseModel):
    """Schema for timestamp reference in response."""
    text: str
    start_time: float
    end_time: float


class SourceReference(BaseModel):
    """Schema for source reference in response."""
    content: str
    page_number: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    message: str
    session_id: UUID
    sources: List[SourceReference] = []
    timestamps: List[TimestampReference] = []


class ChatMessageResponse(BaseModel):
    """Schema for chat message in history."""
    id: UUID
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""
    id: UUID
    title: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    messages: List[ChatMessageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history list."""
    sessions: List[ChatSessionResponse]
    total: int
