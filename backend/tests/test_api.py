"""Tests for API endpoints."""
import io
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/api/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_upload_pdf(client: AsyncClient, sample_pdf_content):
    """Test PDF upload."""
    with patch("app.api.endpoints.upload.file_service") as mock_fs:
        mock_fs.save_file = AsyncMock(
            return_value=("test.pdf", "/tmp/test.pdf", 1024)
        )
        mock_fs.get_file_extension = MagicMock(return_value="pdf")
        mock_fs.get_file_type = MagicMock(return_value="document")
        mock_fs.validate_file = MagicMock(return_value="pdf")

        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
        response = await client.post("/api/upload/", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["file_type"] == "document"
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_unsupported_file(client: AsyncClient):
    """Test uploading unsupported file type."""
    with patch("app.api.endpoints.upload.file_service") as mock_fs:
        from app.core.exceptions import UnsupportedFileTypeError
        mock_fs.save_file = AsyncMock(side_effect=UnsupportedFileTypeError("exe"))

        files = {"file": ("test.exe", io.BytesIO(b"malware"), "application/octet-stream")}
        response = await client.post("/api/upload/", files=files)

        assert response.status_code == 415


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, db_session):
    """Test listing documents."""
    response = await client.get("/api/documents/")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    """Test getting non-existent document."""
    fake_id = uuid4()
    response = await client.get(f"/api/documents/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_media_files(client: AsyncClient):
    """Test listing media files."""
    response = await client.get("/api/media/")
    assert response.status_code == 200
    data = response.json()
    assert "media_files" in data
    assert isinstance(data["media_files"], list)


@pytest.mark.asyncio
async def test_get_media_not_found(client: AsyncClient):
    """Test getting non-existent media file."""
    fake_id = uuid4()
    response = await client.get(f"/api/media/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient):
    """Test chat endpoint."""
    with patch("app.api.endpoints.chat.chat_service") as mock_cs:
        mock_cs.chat = AsyncMock(return_value={
            "message": "Test response",
            "session_id": uuid4(),
            "sources": [],
            "timestamps": [],
        })

        response = await client.post("/api/chat/", json={
            "message": "What is this document about?",
            "source_id": str(uuid4()),
            "source_type": "document",
        })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data


@pytest.mark.asyncio
async def test_chat_empty_message(client: AsyncClient):
    """Test chat with empty message."""
    response = await client.post("/api/chat/", json={
        "message": "",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_chat_sessions(client: AsyncClient):
    """Test listing chat sessions."""
    response = await client.get("/api/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    """Test getting non-existent session."""
    fake_id = uuid4()
    response = await client.get(f"/api/chat/sessions/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(client: AsyncClient):
    """Test deleting non-existent session."""
    fake_id = uuid4()
    response = await client.delete(f"/api/chat/sessions/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_status_not_found(client: AsyncClient):
    """Test getting status for non-existent upload."""
    fake_id = uuid4()
    response = await client.get(f"/api/upload/status/{fake_id}?file_type=document")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_media_timestamps_not_found(client: AsyncClient):
    """Test querying timestamps for non-existent media."""
    fake_id = uuid4()
    response = await client.post(
        f"/api/media/{fake_id}/timestamps",
        json={"query": "test query"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_document_summarize_not_found(client: AsyncClient):
    """Test summarizing non-existent document."""
    fake_id = uuid4()
    response = await client.post(f"/api/documents/{fake_id}/summarize")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_media_summarize_not_found(client: AsyncClient):
    """Test summarizing non-existent media."""
    fake_id = uuid4()
    response = await client.post(f"/api/media/{fake_id}/summarize")
    assert response.status_code == 404
