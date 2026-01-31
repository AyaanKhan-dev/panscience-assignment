"""Chat service for managing conversations and orchestrating Q&A."""
from typing import List, Dict, Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.document import Document
from app.models.media import MediaFile
from app.models.embedding import Embedding
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.core.exceptions import AppException


class ChatService:
    """Service for managing chat sessions and Q&A."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()

    async def create_session(
        self,
        db: AsyncSession,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            title=title,
            source_type=source_type,
            source_id=source_id,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(
        self,
        db: AsyncSession,
        session_id: UUID
    ) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        stmt = select(ChatSession).where(
            ChatSession.id == session_id
        ).options(selectinload(ChatSession.messages))

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sessions(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> List[ChatSession]:
        """Get all chat sessions."""
        stmt = select(ChatSession).order_by(
            ChatSession.updated_at.desc()
        ).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def add_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Add a message to a session."""
        message = ChatMessage(
            session_id=session_id,
            role=MessageRole(role),
            content=content,
            message_metadata=metadata,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    async def chat(
        self,
        db: AsyncSession,
        message: str,
        session_id: Optional[UUID] = None,
        source_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        stream: bool = False
    ) -> Dict | AsyncGenerator[str, None]:
        """
        Process a chat message and return response.

        Returns:
            Dict with 'message', 'session_id', 'sources', and 'timestamps'
        """
        # Get or create session
        if session_id:
            session = await self.get_session(db, session_id)
            if not session:
                raise AppException("Chat session not found", status_code=404)
        else:
            session = await self.create_session(
                db, source_type, source_id, title=message[:50]
            )

        # Save user message
        await self.add_message(db, session.id, "user", message)

        # Get relevant context
        context_chunks = await self.embedding_service.search_similar(
            db,
            query=message,
            source_id=source_id or session.source_id,
            source_type=source_type or session.source_type,
            limit=5,
        )

        # Format context for LLM
        formatted_chunks = []
        sources = []
        timestamps = []

        for emb, score in context_chunks:
            chunk_data = {
                "content": emb.content,
                "page_number": emb.page_number,
                "start_time": emb.start_time,
                "end_time": emb.end_time,
                "score": score,
            }
            formatted_chunks.append(chunk_data)

            # Build source reference
            source = {"content": emb.content[:200] + "..." if len(emb.content) > 200 else emb.content}
            if emb.page_number:
                source["page_number"] = emb.page_number
            if emb.start_time is not None:
                source["start_time"] = emb.start_time
                source["end_time"] = emb.end_time
                timestamps.append({
                    "text": emb.content[:100],
                    "start_time": emb.start_time,
                    "end_time": emb.end_time,
                })
            sources.append(source)

        # Get chat history explicitly to avoid async lazy-loading
        chat_history = []
        history_stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
        history_result = await db.execute(history_stmt)
        history_messages = list(reversed(history_result.scalars().all()))
        for msg in history_messages:
            chat_history.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Get LLM response
        if stream:
            async def stream_response():
                full_response = ""
                async for chunk in await self.llm_service.answer_question(
                    message,
                    formatted_chunks,
                    chat_history,
                    stream=True
                ):
                    full_response += chunk
                    yield chunk

                # Save assistant message after streaming completes
                await self.add_message(
                    db, session.id, "assistant", full_response,
                    metadata={"sources": sources, "timestamps": timestamps}
                )

            return stream_response()
        else:
            response = await self.llm_service.answer_question(
                message,
                formatted_chunks,
                chat_history,
                stream=False
            )

            # Save assistant message
            await self.add_message(
                db, session.id, "assistant", response,
                metadata={"sources": sources, "timestamps": timestamps}
            )

            return {
                "message": response,
                "session_id": session.id,
                "sources": sources,
                "timestamps": timestamps,
            }

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: UUID
    ) -> bool:
        """Delete a chat session."""
        session = await self.get_session(db, session_id)
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False
