"""API routes aggregator."""
from fastapi import APIRouter

from app.api.endpoints import upload, documents, media, chat, health

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(upload.router, prefix="/upload", tags=["Upload"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(media.router, prefix="/media", tags=["Media"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
