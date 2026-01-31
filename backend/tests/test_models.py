"""Tests for database models."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.document import Document, ProcessingStatus
from app.models.media import MediaFile, MediaType, Transcript, TranscriptSegment
from app.models.embedding import Embedding, SourceType
from app.models.chat import ChatSession, ChatMessage, MessageRole


class TestDocumentModel:
    """Tests for Document model."""

    def test_create_document(self):
        """Test document creation."""
        doc = Document(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        assert doc.filename == "test.pdf"
        assert doc.original_filename == "Test Document.pdf"
        assert doc.status == ProcessingStatus.PENDING

    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        assert "Test Document.pdf" in repr(doc)


class TestMediaFileModel:
    """Tests for MediaFile model."""

    def test_create_audio_file(self):
        """Test audio file creation."""
        media = MediaFile(
            filename="test.mp3",
            original_filename="Test Audio.mp3",
            file_path="/uploads/test.mp3",
            file_size=10240,
            mime_type="audio/mpeg",
            media_type=MediaType.AUDIO,
        )

        assert media.media_type == MediaType.AUDIO
        assert media.status.value == "pending"

    def test_create_video_file(self):
        """Test video file creation."""
        media = MediaFile(
            filename="test.mp4",
            original_filename="Test Video.mp4",
            file_path="/uploads/test.mp4",
            file_size=102400,
            mime_type="video/mp4",
            media_type=MediaType.VIDEO,
        )

        assert media.media_type == MediaType.VIDEO


class TestTranscriptModel:
    """Tests for Transcript model."""

    def test_create_transcript(self):
        """Test transcript creation."""
        media_id = uuid4()
        transcript = Transcript(
            media_file_id=media_id,
            full_text="This is a test transcription.",
        )

        assert transcript.media_file_id == media_id
        assert transcript.full_text == "This is a test transcription."


class TestTranscriptSegmentModel:
    """Tests for TranscriptSegment model."""

    def test_create_segment(self):
        """Test transcript segment creation."""
        transcript_id = uuid4()
        segment = TranscriptSegment(
            transcript_id=transcript_id,
            text="Hello world",
            start_time=0.0,
            end_time=1.5,
        )

        assert segment.start_time == 0.0
        assert segment.end_time == 1.5
        assert segment.text == "Hello world"


class TestEmbeddingModel:
    """Tests for Embedding model."""

    def test_create_document_embedding(self):
        """Test document embedding creation."""
        source_id = uuid4()
        embedding = Embedding(
            source_type=SourceType.DOCUMENT,
            source_id=source_id,
            content="Test content chunk",
            chunk_index=0,
            page_number=1,
            embedding=[0.1] * 1536,
        )

        assert embedding.source_type == SourceType.DOCUMENT
        assert embedding.page_number == 1
        assert len(embedding.embedding) == 1536

    def test_create_media_embedding(self):
        """Test media embedding creation."""
        source_id = uuid4()
        embedding = Embedding(
            source_type=SourceType.MEDIA,
            source_id=source_id,
            content="Transcribed content chunk",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            embedding=[0.1] * 1536,
        )

        assert embedding.source_type == SourceType.MEDIA
        assert embedding.start_time == 0.0
        assert embedding.end_time == 10.0


class TestChatModels:
    """Tests for Chat models."""

    def test_create_session(self):
        """Test chat session creation."""
        session = ChatSession(
            title="Test Session",
            source_type="document",
            source_id=uuid4(),
        )

        assert session.title == "Test Session"
        assert session.source_type == "document"

    def test_create_message(self):
        """Test chat message creation."""
        session_id = uuid4()
        message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content="What is this document about?",
        )

        assert message.role == MessageRole.USER
        assert message.content == "What is this document about?"

    def test_message_roles(self):
        """Test message role enumeration."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
