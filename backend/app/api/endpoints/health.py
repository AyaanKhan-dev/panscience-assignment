"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check service health status."""
    # Check database connection
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        pass

    # Redis check would go here
    redis_status = "not_configured"

    overall_status = "healthy" if db_status == "healthy" else "unhealthy"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Powered Document & Multimedia Q&A System",
        "version": "1.0.0",
        "docs": "/docs",
    }
