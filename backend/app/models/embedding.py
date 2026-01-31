"""Embedding model for vector storage."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Enum as SQLEnum, JSON

from app.core.database import Base
from app.core.types import GUID


class SourceType(str, Enum):
    """Source type enumeration."""
    DOCUMENT = "document"
    MEDIA = "media"


class Embedding(Base):
    """Embedding model for storing text chunks and their vector embeddings."""

    __tablename__ = "embeddings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Source reference
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_id = Column(GUID(), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    # For media - timestamp reference
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)

    # For documents - page reference
    page_number = Column(Integer, nullable=True)

    # Embedding vector (stored as JSON for SQLite compatibility)
    # Note: For production, use pgvector extension with ARRAY(Float)
    embedding = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Embedding {self.source_type}:{self.source_id} chunk {self.chunk_index}>"
