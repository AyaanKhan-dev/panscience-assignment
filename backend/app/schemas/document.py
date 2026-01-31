"""Pydantic schemas for document endpoints."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for document creation (used internally)."""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    page_count: Optional[int] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    documents: List[DocumentResponse]
    total: int


class DocumentContentResponse(BaseModel):
    """Schema for document content response."""
    id: UUID
    content: Optional[str] = None
    page_count: Optional[int] = None


class SummaryRequest(BaseModel):
    """Schema for summary generation request."""
    max_length: Optional[int] = Field(default=500, ge=100, le=2000)


class SummaryResponse(BaseModel):
    """Schema for summary response."""
    id: UUID
    summary: str
    source_type: str
