"""Transcription service for audio/video files using OpenAI Whisper."""
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import subprocess

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError

settings = get_settings()


class TranscriptionService:
    """Service for transcribing audio and video files."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.whisper_model

    async def transcribe(
        self,
        file_path: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio/video file using OpenAI Whisper.

        Returns:
            Dict with 'full_text' and 'segments' (with timestamps)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise TranscriptionError(f"File not found: {file_path}")

            # Extract audio if video file
            audio_path = file_path
            temp_audio = None

            if path.suffix.lower() in [".mp4", ".webm"]:
                audio_path = await self._extract_audio(file_path)
                temp_audio = audio_path

            try:
                # Transcribe with Whisper
                with open(audio_path, "rb") as audio_file:
                    response = await self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                        language=language,
                    )

                # Parse response
                segments = []
                if hasattr(response, "segments") and response.segments:
                    for seg in response.segments:
                        segments.append({
                            "text": seg.get("text", "").strip(),
                            "start_time": seg.get("start", 0),
                            "end_time": seg.get("end", 0),
                        })

                return {
                    "full_text": response.text,
                    "segments": segments,
                    "duration": response.duration if hasattr(response, "duration") else None,
                }

            finally:
                # Cleanup temp audio file
                if temp_audio and os.path.exists(temp_audio):
                    os.remove(temp_audio)

        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(str(e))

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        try:
            # Create temp file for audio
            temp_dir = tempfile.gettempdir()
            audio_filename = f"audio_{os.path.basename(video_path)}.mp3"
            audio_path = os.path.join(temp_dir, audio_filename)

            # Run ffmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "libmp3lame",
                "-ab", "128k",
                "-ar", "16000",  # 16kHz for Whisper
                "-y",  # Overwrite
                audio_path
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if process.returncode != 0:
                raise TranscriptionError(f"FFmpeg error: {process.stderr}")

            return audio_path

        except subprocess.TimeoutExpired:
            raise TranscriptionError("Audio extraction timed out")
        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"Failed to extract audio: {str(e)}")

    def chunk_transcript(
        self,
        segments: List[Dict],
        chunk_size: int = None
    ) -> List[Dict]:
        """
        Group transcript segments into larger chunks for embedding.

        Returns:
            List of chunks with combined text and time ranges
        """
        chunk_size = chunk_size or settings.chunk_size

        if not segments:
            return []

        chunks = []
        current_chunk = {
            "content": "",
            "start_time": segments[0]["start_time"],
            "end_time": segments[0]["end_time"],
            "chunk_index": 0,
        }

        for segment in segments:
            segment_text = segment["text"].strip()

            if len(current_chunk["content"]) + len(segment_text) <= chunk_size:
                current_chunk["content"] += " " + segment_text
                current_chunk["end_time"] = segment["end_time"]
            else:
                # Save current chunk
                current_chunk["content"] = current_chunk["content"].strip()
                if current_chunk["content"]:
                    chunks.append(current_chunk)

                # Start new chunk
                current_chunk = {
                    "content": segment_text,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "chunk_index": len(chunks),
                }

        # Add final chunk
        current_chunk["content"] = current_chunk["content"].strip()
        if current_chunk["content"]:
            chunks.append(current_chunk)

        return chunks

    async def get_duration(self, file_path: str) -> float:
        """Get duration of audio/video file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if process.returncode == 0:
                return float(process.stdout.strip())
            return 0.0

        except Exception:
            return 0.0
