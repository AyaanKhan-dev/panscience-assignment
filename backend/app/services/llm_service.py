"""LLM service - works with OpenAI if key provided, otherwise uses context-based responses."""
from typing import List, Dict, Optional, AsyncGenerator

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMError, AppException, RateLimitError

settings = get_settings()


class LLMService:
    """Service for LLM-powered question answering and summarization."""

    def __init__(self):
        self.has_openai = bool(settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here")
        self.client = None
        self.model = settings.openai_model

        if self.has_openai:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def answer_question(
        self,
        question: str,
        context_chunks: List[Dict],
        chat_history: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """
        Answer a question based on provided context.
        Uses OpenAI if available, otherwise returns context-based response.
        """
        try:
            if self.has_openai and self.client:
                return await self._answer_with_openai(question, context_chunks, chat_history, stream)
            return self._answer_from_context(question, context_chunks)
        except AppException:
            raise
        except Exception as e:
            raise LLMError(str(e))

    async def _answer_with_openai(
        self,
        question: str,
        context_chunks: List[Dict],
        chat_history: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Answer using OpenAI API."""
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_text = f"[Source {i}]: {chunk['content']}"
            if chunk.get("page_number"):
                context_text += f" (Page {chunk['page_number']})"
            if chunk.get("start_time") is not None:
                start = self._format_timestamp(chunk["start_time"])
                end = self._format_timestamp(chunk.get("end_time", chunk["start_time"]))
                context_text += f" (Timestamp: {start} - {end})"
            context_parts.append(context_text)

        context = "\n\n".join(context_parts)

        system_prompt = f"""You are a helpful AI assistant that answers questions based strictly on the provided context.

IMPORTANT RULES:
1. Only answer based on the information in the context provided
2. If the answer is not in the context, say "I don't have enough information in the provided content to answer this question."
3. When referencing information, cite the source number (e.g., "According to [Source 1]...")
4. For audio/video content, include relevant timestamps when available
5. Be concise but thorough

CONTEXT:
{context}"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({"role": "user", "content": question})

        if stream:
            return self._stream_response(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            self._raise_if_rate_limited(e)
            raise

    async def _stream_response(
        self,
        messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self._raise_if_rate_limited(e)
            raise LLMError(str(e))

    def _answer_from_context(
        self,
        question: str,
        context_chunks: List[Dict]
    ) -> str:
        """Generate answer from context without LLM (retrieval-based)."""
        if not context_chunks:
            return "I don't have any relevant content to answer this question. Please upload a document or media file first."

        # Build response from most relevant chunks
        response_parts = []
        response_parts.append(f"**Based on the uploaded content, here's what I found relevant to your question:**\n")

        for i, chunk in enumerate(context_chunks[:3], 1):  # Top 3 chunks
            content = chunk['content']

            # Add source info
            source_info = []
            if chunk.get("page_number"):
                source_info.append(f"Page {chunk['page_number']}")
            if chunk.get("start_time") is not None:
                start = self._format_timestamp(chunk["start_time"])
                end = self._format_timestamp(chunk.get("end_time", chunk["start_time"]))
                source_info.append(f"Timestamp: {start} - {end}")

            source_str = f" ({', '.join(source_info)})" if source_info else ""

            # Truncate if too long
            if len(content) > 500:
                content = content[:500] + "..."

            response_parts.append(f"**[Source {i}]{source_str}:**\n{content}\n")

        response_parts.append("\n---\n*Note: For more intelligent responses, please configure an OpenAI API key in the backend .env file.*")

        return "\n".join(response_parts)

    async def generate_summary(
        self,
        content: str,
        max_length: int = 500,
        content_type: str = "document"
    ) -> str:
        """
        Generate a summary of the content.
        Uses OpenAI if available, otherwise uses extractive summary.
        """
        try:
            if self.has_openai and self.client:
                return await self._summarize_with_openai(content, max_length, content_type)
            return self._extractive_summary(content, max_length)
        except AppException:
            raise
        except Exception as e:
            raise LLMError(f"Summary generation failed: {str(e)}")

    async def _summarize_with_openai(
        self,
        content: str,
        max_length: int,
        content_type: str
    ) -> str:
        """Summarize using OpenAI API."""
        type_context = {
            "document": "document/PDF",
            "audio": "audio recording/podcast",
            "video": "video content",
        }

        system_prompt = f"""You are a summarization expert. Create a clear, comprehensive summary of the following {type_context.get(content_type, 'content')}.

GUIDELINES:
1. Capture the main topics and key points
2. Maintain logical flow
3. Keep the summary under {max_length} words
4. Use bullet points for multiple distinct topics
5. Highlight any important conclusions or takeaways"""

        # Truncate content if too long
        max_content = 15000
        if len(content) > max_content:
            content = content[:max_content] + "...[truncated]"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please summarize this content:\n\n{content}"}
                ],
                temperature=0.3,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            self._raise_if_rate_limited(e)
            raise

    def _extractive_summary(self, content: str, max_length: int = 500) -> str:
        """Simple extractive summary without LLM."""
        if not content:
            return "No content available to summarize."

        # Split into sentences
        sentences = content.replace('\n', ' ').split('. ')
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return content[:max_length * 5] + "..." if len(content) > max_length * 5 else content

        # Take first few sentences as summary (usually contain key info)
        summary_sentences = []
        char_count = 0
        target_chars = max_length * 5  # ~5 chars per word

        for sentence in sentences:
            if char_count + len(sentence) < target_chars:
                summary_sentences.append(sentence)
                char_count += len(sentence)
            else:
                break

        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'

        return f"**Summary (Extractive):**\n\n{summary}\n\n---\n*Note: For AI-generated summaries, please configure an OpenAI API key.*"

    async def find_relevant_timestamps(
        self,
        query: str,
        transcript_segments: List[Dict],
        context_chunks: List[Dict]
    ) -> Dict:
        """
        Find relevant timestamps for a query in media content.
        """
        try:
            # Get timestamps from context chunks
            timestamps = []
            for chunk in context_chunks[:3]:
                if chunk.get("start_time") is not None:
                    timestamps.append({
                        "text": chunk["content"][:200],
                        "start_time": chunk["start_time"],
                        "end_time": chunk.get("end_time", chunk["start_time"]),
                        "relevance_score": chunk.get("score", 0.8),
                    })

            if self.has_openai and self.client:
                answer = await self._get_timestamp_answer_openai(query, context_chunks)
            else:
                answer = self._answer_from_context(query, context_chunks)

            return {
                "answer": answer,
                "timestamps": timestamps,
            }
        except AppException:
            raise
        except Exception as e:
            raise LLMError(f"Timestamp search failed: {str(e)}")

    async def _get_timestamp_answer_openai(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> str:
        """Get timestamp-aware answer using OpenAI."""
        context_parts = []
        for chunk in context_chunks:
            if chunk.get("start_time") is not None:
                start = self._format_timestamp(chunk["start_time"])
                end = self._format_timestamp(chunk.get("end_time", chunk["start_time"]))
                context_parts.append(f"[{start} - {end}]: {chunk['content']}")

        context = "\n\n".join(context_parts)

        system_prompt = f"""You are an assistant that helps find relevant parts of audio/video content.
Given the transcript with timestamps, answer the user's question and reference the relevant times.

TRANSCRIPT WITH TIMESTAMPS:
{context}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            self._raise_if_rate_limited(e)
            raise

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS format."""
        if seconds is None:
            return "0:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _raise_if_rate_limited(self, error: Exception) -> None:
        """Raise RateLimitError for 429 responses from OpenAI."""
        if isinstance(error, httpx.HTTPStatusError):
            if error.response is not None and error.response.status_code == 429:
                raise RateLimitError()
            return
        # Fallback for OpenAI SDK exceptions, when available
        try:
            from openai import RateLimitError as OpenAIRateLimitError, APIStatusError
        except Exception:
            OpenAIRateLimitError = None
            APIStatusError = None

        if OpenAIRateLimitError and isinstance(error, OpenAIRateLimitError):
            raise RateLimitError()
        if APIStatusError and isinstance(error, APIStatusError):
            if getattr(error, "status_code", None) == 429:
                raise RateLimitError()
