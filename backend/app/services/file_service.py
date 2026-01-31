"""File handling service for uploads and storage."""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import UnsupportedFileTypeError, FileProcessingError

settings = get_settings()


class FileService:
    """Service for handling file uploads and storage."""

    MIME_TYPE_MAP = {
        "pdf": "application/pdf",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "mp4": "video/mp4",
        "webm": "video/webm",
    }

    AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "ogg"}
    VIDEO_EXTENSIONS = {"mp4", "webm"}

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    def validate_file(self, file: UploadFile) -> str:
        """Validate file type and return extension."""
        extension = self.get_file_extension(file.filename)

        if extension not in settings.allowed_extensions:
            raise UnsupportedFileTypeError(extension)

        return extension

    def get_file_type(self, extension: str) -> str:
        """Determine file type category from extension."""
        if extension == "pdf":
            return "document"
        elif extension in self.AUDIO_EXTENSIONS:
            return "audio"
        elif extension in self.VIDEO_EXTENSIONS:
            return "video"
        else:
            return "unknown"

    def get_media_type(self, extension: str) -> str:
        """Get media type (audio/video) from extension."""
        if extension in self.AUDIO_EXTENSIONS:
            return "audio"
        elif extension in self.VIDEO_EXTENSIONS:
            return "video"
        return "unknown"

    async def save_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Save uploaded file to disk.

        Returns:
            Tuple of (unique_filename, file_path, file_size)
        """
        extension = self.validate_file(file)

        # Generate unique filename
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}.{extension}"
        file_path = self.upload_dir / unique_filename

        # Save file
        try:
            content = await file.read()
            file_size = len(content)

            # Check file size
            max_size = settings.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                raise FileProcessingError(
                    f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed ({settings.max_file_size_mb}MB)"
                )

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            return unique_filename, str(file_path), file_size

        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise
            raise FileProcessingError(f"Failed to save file: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk."""
        try:
            path = Path(file_path)
            if path.exists():
                os.remove(path)
                return True
            return False
        except Exception:
            return False

    def get_file_path(self, filename: str) -> Path:
        """Get full path for a filename."""
        return self.upload_dir / filename

    def file_exists(self, filename: str) -> bool:
        """Check if file exists."""
        return (self.upload_dir / filename).exists()
