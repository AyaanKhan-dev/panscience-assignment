"""PDF processing service for text extraction."""
from pathlib import Path
from typing import List, Tuple
import io

import pdfplumber
from PyPDF2 import PdfReader

from app.core.config import get_settings
from app.core.exceptions import FileProcessingError

settings = get_settings()


class PDFService:
    """Service for PDF text extraction and processing."""

    async def extract_text(self, file_path: str) -> Tuple[str, int]:
        """
        Extract text content from PDF file.

        Returns:
            Tuple of (extracted_text, page_count)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileProcessingError(f"PDF file not found: {file_path}")

            full_text = []
            page_count = 0

            # Use pdfplumber for better text extraction
            with pdfplumber.open(path) as pdf:
                page_count = len(pdf.pages)

                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(f"[Page {i}]\n{text}")

            extracted_text = "\n\n".join(full_text)

            if not extracted_text.strip():
                # Fallback to PyPDF2
                extracted_text, page_count = await self._extract_with_pypdf2(path)

            return extracted_text, page_count

        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise
            raise FileProcessingError(f"Failed to extract text from PDF: {str(e)}")

    async def _extract_with_pypdf2(self, path: Path) -> Tuple[str, int]:
        """Fallback extraction using PyPDF2."""
        try:
            reader = PdfReader(path)
            page_count = len(reader.pages)
            full_text = []

            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    full_text.append(f"[Page {i}]\n{text}")

            return "\n\n".join(full_text), page_count
        except Exception as e:
            raise FileProcessingError(f"PyPDF2 extraction failed: {str(e)}")

    def chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[dict]:
        """
        Split text into chunks with overlap.

        Returns:
            List of dicts with 'content', 'chunk_index', and optional 'page_number'
        """
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap

        if not text:
            return []

        chunks = []
        current_page = 1

        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # Track page numbers
            if para.startswith("[Page "):
                try:
                    page_marker = para.split("]")[0]
                    current_page = int(page_marker.replace("[Page ", ""))
                except (ValueError, IndexError):
                    pass

            # Add paragraph to current chunk
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "page_number": current_page,
                    })
                    chunk_index += 1

                # Start new chunk with overlap
                if chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "page_number": current_page,
            })

        return chunks

    async def get_page_text(self, file_path: str, page_number: int) -> str:
        """Extract text from a specific page."""
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise FileProcessingError(f"Page {page_number} not found")

                page = pdf.pages[page_number - 1]
                return page.extract_text() or ""
        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise
            raise FileProcessingError(f"Failed to extract page text: {str(e)}")
