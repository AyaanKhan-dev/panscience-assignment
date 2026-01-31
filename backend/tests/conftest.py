"""Pytest configuration and fixtures."""
import asyncio
import os
import tempfile
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings

settings = get_settings()

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client():
    """Create synchronous test client."""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF bytes."""
    # Minimal valid PDF
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
0
%%EOF"""


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.AsyncOpenAI") as mock:
        client = AsyncMock()

        # Mock embeddings
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
        client.embeddings.create = AsyncMock(return_value=embedding_response)

        # Mock chat completions
        chat_response = MagicMock()
        chat_response.choices = [
            MagicMock(message=MagicMock(content="This is a test response."))
        ]
        client.chat.completions.create = AsyncMock(return_value=chat_response)

        # Mock transcription
        transcription_response = MagicMock()
        transcription_response.text = "This is test transcription."
        transcription_response.segments = [
            {"text": "This is", "start": 0.0, "end": 1.0},
            {"text": "test transcription.", "start": 1.0, "end": 2.0},
        ]
        transcription_response.duration = 2.0
        client.audio.transcriptions.create = AsyncMock(
            return_value=transcription_response
        )

        mock.return_value = client
        yield client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    with patch("app.services.embedding_service.EmbeddingService") as mock:
        service = MagicMock()
        service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        service.generate_embeddings_batch = AsyncMock(
            return_value=[[0.1] * 1536]
        )
        service.store_embeddings = AsyncMock(return_value=1)
        service.search_similar = AsyncMock(return_value=[])
        mock.return_value = service
        yield service


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "id": uuid4(),
        "filename": "test.pdf",
        "original_filename": "test_document.pdf",
        "file_path": "/tmp/test.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "content": "This is test content from a PDF document.",
        "page_count": 1,
    }


@pytest.fixture
def sample_media_data():
    """Sample media data for testing."""
    return {
        "id": uuid4(),
        "filename": "test.mp3",
        "original_filename": "test_audio.mp3",
        "file_path": "/tmp/test.mp3",
        "file_size": 10240,
        "mime_type": "audio/mpeg",
        "media_type": "audio",
        "duration": 120.0,
    }
