"""Media models for audio and video files."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import GUID


class MediaType(str, Enum):
    """Media type enumeration."""
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaFile(Base):
    """Media file model for audio and video."""

    __tablename__ = "media_files"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    media_type = Column(SQLEnum(MediaType), nullable=False)

    # Media metadata
    duration = Column(Float, nullable=True)  # Duration in seconds

    # Processing status
    status = Column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    error_message = Column(Text, nullable=True)

    # Summary
    summary = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    transcript = relationship("Transcript", back_populates="media_file", uselist=False)

    def __repr__(self):
        return f"<MediaFile {self.original_filename}>"


class Transcript(Base):
    """Transcript model for storing transcription with timestamps."""

    __tablename__ = "transcripts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    media_file_id = Column(GUID(), ForeignKey("media_files.id"), nullable=False)

    # Full transcription text
    full_text = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    media_file = relationship("MediaFile", back_populates="transcript")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transcript for {self.media_file_id}>"


class TranscriptSegment(Base):
    """Individual transcript segment with timestamp."""

    __tablename__ = "transcript_segments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(GUID(), ForeignKey("transcripts.id"), nullable=False)

    # Segment content
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)    # End time in seconds

    # Relationships
    transcript = relationship("Transcript", back_populates="segments")

    def __repr__(self):
        return f"<TranscriptSegment {self.start_time}-{self.end_time}>"
