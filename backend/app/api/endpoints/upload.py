"""File upload endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnsupportedFileTypeError, FileProcessingError
from app.services.file_service import FileService
from app.services.pdf_service import PDFService
from app.services.transcription_service import TranscriptionService
from app.services.embedding_service import EmbeddingService
from app.models.document import Document, ProcessingStatus
from app.models.media import MediaFile, MediaType, ProcessingStatus as MediaStatus, Transcript, TranscriptSegment
from app.schemas.common import UploadResponse, StatusResponse

router = APIRouter()
file_service = FileService()
pdf_service = PDFService()
transcription_service = TranscriptionService()
embedding_service = EmbeddingService()


async def process_document(
    document_id: UUID,
    file_path: str,
    db: AsyncSession
):
    """Background task to process a PDF document."""
    try:
        # Get document
        document = await db.get(Document, document_id)
        if not document:
            return

        document.status = ProcessingStatus.PROCESSING
        await db.commit()

        # Extract text
        content, page_count = await pdf_service.extract_text(file_path)
        document.content = content
        document.page_count = page_count

        # Chunk and embed
        chunks = pdf_service.chunk_text(content)
        await embedding_service.store_embeddings(
            db, "document", document_id, chunks
        )

        document.status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()
        await db.commit()

    except Exception as e:
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        await db.commit()


async def process_media(
    media_id: UUID,
    file_path: str,
    db: AsyncSession
):
    """Background task to process audio/video file."""
    try:
        # Get media file
        media = await db.get(MediaFile, media_id)
        if not media:
            return

        media.status = MediaStatus.PROCESSING
        await db.commit()

        # Get duration
        duration = await transcription_service.get_duration(file_path)
        media.duration = duration

        # Transcribe
        result = await transcription_service.transcribe(file_path)

        # Create transcript record
        transcript = Transcript(
            media_file_id=media_id,
            full_text=result["full_text"],
        )
        db.add(transcript)
        await db.flush()

        # Add segments
        for seg in result["segments"]:
            segment = TranscriptSegment(
                transcript_id=transcript.id,
                text=seg["text"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
            )
            db.add(segment)

        # Chunk transcript and embed
        chunks = transcription_service.chunk_transcript(result["segments"])
        await embedding_service.store_embeddings(
            db, "media", media_id, chunks
        )

        media.status = MediaStatus.COMPLETED
        media.processed_at = datetime.utcnow()
        await db.commit()

    except Exception as e:
        media.status = MediaStatus.FAILED
        media.error_message = str(e)
        await db.commit()


@router.post("/", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file (PDF, audio, or video) for processing.

    The file will be processed in the background:
    - PDFs: Text extraction and embedding
    - Audio/Video: Transcription with timestamps and embedding
    """
    try:
        # Save file
        unique_filename, file_path, file_size = await file_service.save_file(file)
        extension = file_service.get_file_extension(file.filename)
        file_type = file_service.get_file_type(extension)

        if file_type == "document":
            # Create document record
            document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/pdf",
                status=ProcessingStatus.PENDING,
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)

            # Schedule background processing
            background_tasks.add_task(
                process_document, document.id, file_path, db
            )

            return UploadResponse(
                id=document.id,
                filename=file.filename,
                file_type="document",
                status="pending",
                message="Document uploaded. Processing started.",
            )

        elif file_type in ["audio", "video"]:
            # Create media record
            media = MediaFile(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                media_type=MediaType(file_service.get_media_type(extension)),
                status=MediaStatus.PENDING,
            )
            db.add(media)
            await db.commit()
            await db.refresh(media)

            # Schedule background processing
            background_tasks.add_task(
                process_media, media.id, file_path, db
            )

            return UploadResponse(
                id=media.id,
                filename=file.filename,
                file_type=file_type,
                status="pending",
                message=f"{file_type.capitalize()} uploaded. Processing started.",
            )

        else:
            raise UnsupportedFileTypeError(extension)

    except (UnsupportedFileTypeError, FileProcessingError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/status/{file_id}", response_model=StatusResponse)
async def get_processing_status(
    file_id: UUID,
    file_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the processing status of an uploaded file."""
    if file_type == "document":
        record = await db.get(Document, file_id)
    else:
        record = await db.get(MediaFile, file_id)

    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    return StatusResponse(
        id=record.id,
        status=record.status.value,
        error_message=record.error_message,
    )
