"""Tests for service layer."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.services.file_service import FileService
from app.services.pdf_service import PDFService
from app.services.transcription_service import TranscriptionService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.core.exceptions import (
    UnsupportedFileTypeError,
    FileProcessingError,
    TranscriptionError,
    EmbeddingError,
    LLMError,
)


class TestFileService:
    """Tests for FileService."""

    def test_get_file_extension(self):
        """Test file extension extraction."""
        service = FileService()
        assert service.get_file_extension("test.pdf") == "pdf"
        assert service.get_file_extension("document.PDF") == "pdf"
        assert service.get_file_extension("audio.mp3") == "mp3"
        assert service.get_file_extension("video.mp4") == "mp4"
        assert service.get_file_extension("noextension") == ""

    def test_get_file_type(self):
        """Test file type detection."""
        service = FileService()
        assert service.get_file_type("pdf") == "document"
        assert service.get_file_type("mp3") == "audio"
        assert service.get_file_type("wav") == "audio"
        assert service.get_file_type("mp4") == "video"
        assert service.get_file_type("webm") == "video"
        assert service.get_file_type("exe") == "unknown"

    def test_get_media_type(self):
        """Test media type detection."""
        service = FileService()
        assert service.get_media_type("mp3") == "audio"
        assert service.get_media_type("mp4") == "video"
        assert service.get_media_type("pdf") == "unknown"


class TestPDFService:
    """Tests for PDFService."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        service = PDFService()
        text = "This is a test paragraph.\n\nThis is another paragraph."
        chunks = service.chunk_text(text, chunk_size=100, chunk_overlap=10)

        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all("chunk_index" in c for c in chunks)

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        service = PDFService()
        chunks = service.chunk_text("", chunk_size=100, chunk_overlap=10)
        assert chunks == []

    def test_chunk_text_with_pages(self):
        """Test chunking with page markers."""
        service = PDFService()
        text = "[Page 1]\nFirst page content.\n\n[Page 2]\nSecond page content."
        chunks = service.chunk_text(text, chunk_size=100, chunk_overlap=10)

        assert len(chunks) > 0


class TestTranscriptionService:
    """Tests for TranscriptionService."""

    def test_chunk_transcript(self):
        """Test transcript chunking."""
        service = TranscriptionService()
        segments = [
            {"text": "Hello world.", "start_time": 0.0, "end_time": 1.0},
            {"text": "How are you?", "start_time": 1.0, "end_time": 2.0},
            {"text": "I am fine.", "start_time": 2.0, "end_time": 3.0},
        ]
        chunks = service.chunk_transcript(segments, chunk_size=50)

        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all("start_time" in c for c in chunks)
        assert all("end_time" in c for c in chunks)

    def test_chunk_transcript_empty(self):
        """Test chunking empty segments."""
        service = TranscriptionService()
        chunks = service.chunk_transcript([])
        assert chunks == []


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test embedding generation."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            client = AsyncMock()
            response = MagicMock()
            response.data = [MagicMock(embedding=[0.1] * 1536)]
            client.embeddings.create = AsyncMock(return_value=response)
            mock_openai.return_value = client

            service = EmbeddingService()
            embedding = await service.generate_embedding("Test text")

            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_empty(self):
        """Test embedding with empty text."""
        with patch("openai.AsyncOpenAI"):
            service = EmbeddingService()
            with pytest.raises(EmbeddingError):
                await service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        import numpy as np
        service = EmbeddingService()

        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        assert service._cosine_similarity(vec1, vec2) == pytest.approx(1.0)

        vec3 = np.array([0.0, 1.0, 0.0])
        assert service._cosine_similarity(vec1, vec3) == pytest.approx(0.0)


class TestLLMService:
    """Tests for LLMService."""

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        service = LLMService()
        assert service._format_timestamp(0) == "0:00"
        assert service._format_timestamp(65) == "1:05"
        assert service._format_timestamp(3665) == "1:01:05"
        assert service._format_timestamp(None) == "0:00"

    @pytest.mark.asyncio
    async def test_answer_question(self):
        """Test question answering."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            client = AsyncMock()
            response = MagicMock()
            response.choices = [
                MagicMock(message=MagicMock(content="Test answer"))
            ]
            client.chat.completions.create = AsyncMock(return_value=response)
            mock_openai.return_value = client

            service = LLMService()
            context = [{"content": "Test context", "page_number": 1}]
            answer = await service.answer_question(
                "Test question?",
                context,
                stream=False
            )

            assert answer == "Test answer"

    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test summary generation."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            client = AsyncMock()
            response = MagicMock()
            response.choices = [
                MagicMock(message=MagicMock(content="Test summary"))
            ]
            client.chat.completions.create = AsyncMock(return_value=response)
            mock_openai.return_value = client

            service = LLMService()
            summary = await service.generate_summary(
                "Long content to summarize...",
                max_length=100,
            )

            assert summary == "Test summary"
