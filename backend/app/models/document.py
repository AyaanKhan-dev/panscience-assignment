"""Document model for PDF files."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SQLEnum

from app.core.database import Base
from app.core.types import GUID


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document model for storing PDF metadata and extracted content."""

    __tablename__ = "documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Extracted content
    content = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)

    # Processing status
    status = Column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    error_message = Column(Text, nullable=True)

    # Metadata
    summary = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Document {self.original_filename}>"
