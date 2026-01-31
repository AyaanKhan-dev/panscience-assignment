"""Document management endpoints."""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.document import Document
from app.services.llm_service import LLMService
from app.services.file_service import FileService
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentContentResponse,
    SummaryRequest,
    SummaryResponse,
)

router = APIRouter()
llm_service = LLMService()
file_service = FileService()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all uploaded documents."""
    stmt = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    # Get total count
    count_stmt = select(Document)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get document details by ID."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/content", response_model=DocumentContentResponse)
async def get_document_content(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get extracted content of a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentContentResponse(
        id=document.id,
        content=document.content,
        page_count=document.page_count,
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download the original document file."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not file_service.file_exists(document.filename):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type=document.mime_type,
    )


@router.post("/{document_id}/summarize", response_model=SummaryResponse)
async def summarize_document(
    document_id: UUID,
    request: Optional[SummaryRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a summary of the document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.content:
        raise HTTPException(
            status_code=400,
            detail="Document has not been processed yet"
        )

    # Check if summary already exists and no specific request
    if document.summary and not request:
        return SummaryResponse(
            id=document.id,
            summary=document.summary,
            source_type="document",
        )

    # Generate summary
    max_length = request.max_length if request else 500
    summary = await llm_service.generate_summary(
        document.content,
        max_length=max_length,
        content_type="document",
    )

    # Save summary
    document.summary = summary
    await db.commit()

    return SummaryResponse(
        id=document.id,
        summary=summary,
        source_type="document",
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its associated data."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    await file_service.delete_file(document.file_path)

    # Delete from database (embeddings will cascade)
    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"}
