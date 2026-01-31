"""Media file management endpoints."""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.media import MediaFile, Transcript
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.file_service import FileService
from app.schemas.media import (
    MediaFileResponse,
    TranscriptResponse,
    TimestampQueryRequest,
    TimestampQueryResponse,
    TimestampResult,
)
from app.schemas.document import SummaryRequest, SummaryResponse

router = APIRouter()
llm_service = LLMService()
embedding_service = EmbeddingService()
file_service = FileService()


@router.get("/")
async def list_media_files(
    skip: int = 0,
    limit: int = 50,
    media_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all uploaded media files."""
    stmt = select(MediaFile).order_by(MediaFile.created_at.desc())

    if media_type:
        stmt = stmt.where(MediaFile.media_type == media_type)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    media_files = result.scalars().all()

    return {
        "media_files": [MediaFileResponse.model_validate(m) for m in media_files],
        "total": len(media_files),
    }


@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media_file(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get media file details by ID."""
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    return MediaFileResponse.model_validate(media)


@router.get("/{media_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the transcript of a media file."""
    stmt = select(Transcript).where(
        Transcript.media_file_id == media_id
    ).options(selectinload(Transcript.segments))

    result = await db.execute(stmt)
    transcript = result.scalar_one_or_none()

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found. File may still be processing."
        )

    return TranscriptResponse.model_validate(transcript)


@router.get("/{media_id}/stream")
async def stream_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Stream media file for playback."""
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    if not file_service.file_exists(media.filename):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=media.file_path,
        media_type=media.mime_type,
        filename=media.original_filename,
    )


@router.post("/{media_id}/timestamps", response_model=TimestampQueryResponse)
async def query_timestamps(
    media_id: UUID,
    request: TimestampQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Query for relevant timestamps in a media file.

    Returns the answer along with relevant timestamp ranges.
    """
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    # Get relevant chunks
    similar_chunks = await embedding_service.search_similar(
        db,
        query=request.query,
        source_id=media_id,
        source_type="media",
        limit=5,
    )

    if not similar_chunks:
        return TimestampQueryResponse(
            query=request.query,
            results=[],
            answer="No relevant content found for this query.",
        )

    # Format chunks for LLM
    context_chunks = []
    for emb, score in similar_chunks:
        context_chunks.append({
            "content": emb.content,
            "start_time": emb.start_time,
            "end_time": emb.end_time,
            "score": score,
        })

    # Get transcript segments
    stmt = select(Transcript).where(
        Transcript.media_file_id == media_id
    ).options(selectinload(Transcript.segments))

    result = await db.execute(stmt)
    transcript = result.scalar_one_or_none()

    transcript_segments = []
    if transcript and transcript.segments:
        transcript_segments = [
            {
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
            }
            for seg in transcript.segments
        ]

    # Get answer with timestamps
    result = await llm_service.find_relevant_timestamps(
        request.query,
        transcript_segments,
        context_chunks,
    )

    return TimestampQueryResponse(
        query=request.query,
        results=[TimestampResult(**ts) for ts in result["timestamps"]],
        answer=result["answer"],
    )


@router.get("/{media_id}/timestamps")
async def get_timestamps_by_query(
    media_id: UUID,
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Query timestamps via GET request."""
    request = TimestampQueryRequest(query=query)
    return await query_timestamps(media_id, request, db)


@router.post("/{media_id}/summarize", response_model=SummaryResponse)
async def summarize_media(
    media_id: UUID,
    request: Optional[SummaryRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a summary of the media file transcript."""
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    # Check if summary already exists
    if media.summary and not request:
        return SummaryResponse(
            id=media.id,
            summary=media.summary,
            source_type=media.media_type.value,
        )

    # Get transcript
    stmt = select(Transcript).where(Transcript.media_file_id == media_id)
    result = await db.execute(stmt)
    transcript = result.scalar_one_or_none()

    if not transcript or not transcript.full_text:
        raise HTTPException(
            status_code=400,
            detail="Media file has not been transcribed yet"
        )

    # Generate summary
    max_length = request.max_length if request else 500
    summary = await llm_service.generate_summary(
        transcript.full_text,
        max_length=max_length,
        content_type=media.media_type.value,
    )

    # Save summary
    media.summary = summary
    await db.commit()

    return SummaryResponse(
        id=media.id,
        summary=summary,
        source_type=media.media_type.value,
    )


@router.delete("/{media_id}")
async def delete_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a media file and its associated data."""
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    # Delete file from disk
    await file_service.delete_file(media.file_path)

    # Delete from database (transcript and embeddings will cascade)
    await db.delete(media)
    await db.commit()

    return {"message": "Media file deleted successfully"}
