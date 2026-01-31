"""Chat and Q&A endpoints."""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatHistoryResponse,
)

router = APIRouter()


def get_chat_service():
    """Get or create chat service lazily."""
    return ChatService()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    chat_service = get_chat_service()
    """
    Send a message and get an AI response.

    The response is grounded in the uploaded content specified by source_id.
    If no source_id is provided, the system will use the session's associated source.
    """
    try:
        result = await chat_service.chat(
            db=db,
            message=request.message,
            session_id=request.session_id,
            source_id=request.source_id,
            source_type=request.source_type,
            stream=False,
        )

        return ChatResponse(
            message=result["message"],
            session_id=result["session_id"],
            sources=result["sources"],
            timestamps=result["timestamps"],
        )

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and stream the AI response.

    Uses Server-Sent Events (SSE) to stream the response.
    """
    chat_service = get_chat_service()
    try:
        async def generate():
            async for chunk in await chat_service.chat(
                db=db,
                message=request.message,
                session_id=request.session_id,
                source_id=request.source_id,
                source_type=request.source_type,
                stream=True,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=ChatHistoryResponse)
async def list_sessions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions."""
    chat_service = get_chat_service()
    sessions = await chat_service.get_sessions(db, limit=limit)

    return ChatHistoryResponse(
        sessions=[ChatSessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a chat session with its messages."""
    chat_service = get_chat_service()
    session = await chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    chat_service = get_chat_service()
    deleted = await chat_service.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted successfully"}
