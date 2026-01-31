"""Embedding service using free local sentence-transformers."""
import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError
from app.models.embedding import Embedding, SourceType

settings = get_settings()

# Global model instance (loaded once)
_model = None


def get_model():
    """Get or create the embedding model (singleton)."""
    global _model
    if _model is None:
        # Use a small, fast model that works well for semantic search
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


class EmbeddingService:
    """Service for generating and managing embeddings using local models."""

    def __init__(self):
        self.model = get_model()
        self.dimension = 384  # all-MiniLM-L6-v2 dimension

    def _encode_sync(self, text: str) -> np.ndarray:
        """Synchronous encoding - runs in thread pool."""
        return self.model.encode(text, convert_to_numpy=True)

    def _encode_batch_sync(self, texts: List[str]) -> np.ndarray:
        """Synchronous batch encoding - runs in thread pool."""
        return self.model.encode(texts, convert_to_numpy=True)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        try:
            if not text.strip():
                raise EmbeddingError("Cannot generate embedding for empty text")

            # Run encoding in thread pool to avoid blocking async context
            embedding = await asyncio.to_thread(self._encode_sync, text)
            return embedding.tolist()

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(str(e))

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if not texts:
                return []

            # Filter empty texts
            valid_texts = [t for t in texts if t.strip()]
            if not valid_texts:
                raise EmbeddingError("No valid texts to embed")

            # Run encoding in thread pool to avoid blocking async context
            embeddings = await asyncio.to_thread(self._encode_batch_sync, valid_texts)
            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(str(e))

    async def store_embeddings(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: UUID,
        chunks: List[Dict],
    ) -> int:
        """
        Generate and store embeddings for chunks.

        Returns:
            Number of embeddings stored
        """
        try:
            if not chunks:
                return 0

            # Generate embeddings in batch
            texts = [chunk["content"] for chunk in chunks]
            embeddings = await self.generate_embeddings_batch(texts)

            # Create embedding records
            for chunk, embedding in zip(chunks, embeddings):
                embedding_record = Embedding(
                    source_type=SourceType(source_type),
                    source_id=source_id,
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    start_time=chunk.get("start_time"),
                    end_time=chunk.get("end_time"),
                    page_number=chunk.get("page_number"),
                    embedding=embedding,
                )
                db.add(embedding_record)

            await db.commit()
            return len(embeddings)

        except Exception as e:
            await db.rollback()
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to store embeddings: {str(e)}")

    async def search_similar(
        self,
        db: AsyncSession,
        query: str,
        source_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Tuple[Embedding, float]]:
        """
        Search for similar embeddings using cosine similarity.

        Returns:
            List of (Embedding, similarity_score) tuples
        """
        try:
            # First, fetch all embeddings from database
            stmt = select(Embedding)

            if source_id:
                stmt = stmt.where(Embedding.source_id == source_id)
            if source_type:
                stmt = stmt.where(Embedding.source_type == SourceType(source_type))

            result = await db.execute(stmt)
            embeddings = result.scalars().all()

            if not embeddings:
                return []

            # Extract all data while in session context to avoid lazy loading
            embedding_data = []
            for emb in embeddings:
                if emb.embedding:
                    # Access all needed attributes now
                    data = {
                        'id': emb.id,
                        'content': emb.content,
                        'page_number': emb.page_number,
                        'start_time': emb.start_time,
                        'end_time': emb.end_time,
                        'embedding': emb.embedding,
                        'obj': emb,
                    }
                    embedding_data.append(data)

            if not embedding_data:
                return []

            # Generate query embedding in thread pool to avoid blocking async context
            query_embedding = await asyncio.to_thread(self._encode_sync, query)
            query_vec = np.array(query_embedding)

            # Calculate cosine similarity
            similarities = []
            for data in embedding_data:
                emb_vec = np.array(data['embedding'])
                similarity = self._cosine_similarity(query_vec, emb_vec)
                similarities.append((data['obj'], similarity))

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Similarity search failed: {str(e)}")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def delete_embeddings(
        self,
        db: AsyncSession,
        source_id: UUID
    ) -> int:
        """Delete all embeddings for a source."""
        try:
            stmt = select(Embedding).where(Embedding.source_id == source_id)
            result = await db.execute(stmt)
            embeddings = result.scalars().all()

            count = len(embeddings)
            for emb in embeddings:
                await db.delete(emb)

            await db.commit()
            return count

        except Exception as e:
            await db.rollback()
            raise EmbeddingError(f"Failed to delete embeddings: {str(e)}")

    async def get_embeddings_count(
        self,
        db: AsyncSession,
        source_id: UUID
    ) -> int:
        """Get count of embeddings for a source."""
        stmt = select(Embedding).where(Embedding.source_id == source_id)
        result = await db.execute(stmt)
        return len(result.scalars().all())
