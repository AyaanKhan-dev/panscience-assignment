# AI-Powered Document & Multimedia Q&A System

A full-stack web application that enables users to upload PDF documents, audio files, and video files, then interact with an AI-powered chatbot to ask questions grounded strictly in the uploaded content.

## Features

- **Multi-format Upload**: Support for PDFs, audio (MP3, WAV, M4A), and video (MP4, WebM)
- **AI-Powered Q&A**: Ask questions about uploaded content with answers grounded in the source material
- **Automatic Transcription**: Audio and video files are transcribed using OpenAI Whisper
- **Timestamped Responses**: Media queries return relevant timestamps with playback seeking
- **Content Summarization**: Generate summaries for any uploaded document or media
- **Real-time Processing**: Background processing with status updates
- **Interactive Media Player**: Built-in player with timestamp navigation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Upload  │  │    Chat      │  │   Media    │  │  Summary  │ │
│  │   UI     │  │  Interface   │  │   Player   │  │   Panel   │ │
│  └──────────┘  └──────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      API Routes                           │  │
│  │  /upload  /documents  /media  /chat  /health             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Services                             │  │
│  │  FileService  PDFService  TranscriptionService           │  │
│  │  EmbeddingService  LLMService  ChatService               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ PostgreSQL│   │   Redis   │   │  OpenAI   │
       │ (pgvector)│   │  (cache)  │   │    API    │
       └───────────┘   └───────────┘   └───────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector for embeddings
- **Caching**: Redis
- **LLM**: OpenAI GPT-4o-mini via LangChain
- **Embeddings**: OpenAI text-embedding-3-small
- **Transcription**: OpenAI Whisper API
- **PDF Processing**: pdfplumber, PyPDF2

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Media Player**: react-player

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd panscience-assignment
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Documentation

### Endpoints

#### Upload
- `POST /api/upload/` - Upload a file (PDF, audio, or video)
- `GET /api/upload/status/{file_id}` - Get processing status

#### Documents
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/content` - Get extracted content
- `POST /api/documents/{id}/summarize` - Generate summary
- `DELETE /api/documents/{id}` - Delete document

#### Media
- `GET /api/media/` - List all media files
- `GET /api/media/{id}` - Get media details
- `GET /api/media/{id}/transcript` - Get transcript
- `GET /api/media/{id}/stream` - Stream media file
- `POST /api/media/{id}/timestamps` - Query timestamps
- `POST /api/media/{id}/summarize` - Generate summary
- `DELETE /api/media/{id}` - Delete media

#### Chat
- `POST /api/chat/` - Send a message
- `POST /api/chat/stream` - Stream response (SSE)
- `GET /api/chat/sessions` - List sessions
- `GET /api/chat/sessions/{id}` - Get session
- `DELETE /api/chat/sessions/{id}` - Delete session

#### Health
- `GET /api/health` - Health check

### Example Requests

**Upload a PDF:**
```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the main topic of this document?",
    "source_id": "file-uuid-here",
    "source_type": "document"
  }'
```

## Testing

### Backend Tests
```bash
cd backend
pytest --cov=app --cov-report=term-missing -v
```

### Frontend Tests
```bash
cd frontend
npm run test:coverage
```

## CI/CD Pipeline

The project uses GitHub Actions for CI/CD:

1. **On Pull Request / Push:**
   - Lint backend (black, isort, flake8)
   - Lint frontend (ESLint)
   - Run backend tests with coverage
   - Run frontend tests
   - Build Docker images

2. **On Main Branch:**
   - All above steps
   - Deploy to production (configurable)

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, database, exceptions
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Helpers
│   ├── tests/            # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API services
│   │   ├── store/        # Zustand store
│   │   ├── types/        # TypeScript types
│   │   └── utils/        # Utilities
│   ├── Dockerfile
│   └── package.json
├── .github/workflows/    # CI/CD
├── docker-compose.yml
├── README.md
└── TODO.md
```

## Design Decisions & Tradeoffs

### Architectural Choices

1. **PostgreSQL over MongoDB**
   - Chose PostgreSQL for strong consistency and pgvector support
   - Better for structured document/media metadata
   - pgvector enables efficient similarity search without external service

2. **FastAPI over Flask/Django**
   - Native async support for better I/O handling
   - Built-in OpenAPI documentation
   - Type hints with Pydantic validation

3. **Zustand over Redux**
   - Simpler API with less boilerplate
   - Sufficient for this application's state complexity
   - Better TypeScript integration

4. **Background Tasks over Celery**
   - Simpler setup for MVP
   - FastAPI's BackgroundTasks is sufficient for current scale
   - Can migrate to Celery if needed

### Tradeoffs

1. **Embedding Storage**
   - Storing as ARRAY(Float) in PostgreSQL
   - For production, migrate to pgvector extension
   - Consider Pinecone for very large scale

2. **Chunking Strategy**
   - Fixed-size chunks with overlap
   - Could use semantic chunking for better results
   - Current approach is simpler and works well

3. **Streaming Responses**
   - SSE for chat streaming
   - Could use WebSockets for bidirectional
   - SSE is simpler and sufficient for Q&A

## Limitations

1. **File Size**: Limited to 100MB per file
2. **Concurrent Processing**: Background tasks run sequentially
3. **Language Support**: Optimized for English content
4. **Vector Search**: Basic cosine similarity (no ANN)

## Future Improvements

1. **Multi-language Support**: Add language detection and translation
2. **Advanced RAG**: Implement hybrid search (keyword + semantic)
3. **User Authentication**: Add user accounts and file ownership
4. **Real-time Collaboration**: Multiple users on same document
5. **Export Features**: Export chat history, annotations
6. **Mobile App**: React Native or PWA
7. **Analytics Dashboard**: Usage metrics and insights
8. **OCR Support**: Handle scanned PDFs
9. **Batch Processing**: Queue system for multiple files
10. **Fine-tuning**: Custom models for specific domains

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

Built for the SDE-1 Programming Assignment
