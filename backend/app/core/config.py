"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "AI Document Q&A System"
    debug: bool = False
    api_prefix: str = "/api"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/docqa"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Whisper/Transcription
    whisper_model: str = "whisper-1"

    # File storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 100
    allowed_extensions: list = ["pdf", "mp3", "wav", "mp4", "webm", "m4a", "ogg"]

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
