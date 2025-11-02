# Multimodal RAG Backend

A FastAPI backend for a Multimodal RAG (Retrieval-Augmented Generation) system that processes PDF documents and provides intelligent, citation-based answers using Google Gemini and Ollama embeddings.

## Features

- PDF document processing (text, tables, images)
- Multimodal RAG with vector search (ChromaDB)
- Google Gemini integration for chat and summarization
- Ollama embeddings for semantic search
- RESTful API with streaming support
- Source citations with relevance scores
- Persistent chat sessions with message history

## Prerequisites

- Python 3.11+
- Ollama installed and running (for embeddings)
- Google Gemini API key
- Poetry (recommended) or pip

## Setup

1. Install Ollama and pull the embedding model:
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull embeddinggemma:latest
```

2. Install dependencies:
```bash
cd backend
poetry install --no-root
# OR
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Run (dev)

Recommended: Poetry

```bash
cd backend
poetry env use 3.11
poetry install --no-root
# Fast dev reload (Ctrl+C may need to be pressed twice)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run without reload for clean Ctrl+C behavior
# poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Alternatively (pip):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API base: `/api`
- Health: `GET /api/health`

## API Endpoints

### Document Management
- `POST /api/upload` - Upload and process a PDF document
- `GET /api/documents` - List all uploaded documents
- `DELETE /api/documents/{doc_id}` - Delete a document and its vectors

### Chat
- `POST /api/chat` - Send a chat message (non-streaming)
- `GET /api/chat/stream` - Stream chat responses
- `GET /api/chat/messages/{session_id}` - Get chat history
- `GET /api/chat/sessions` - List all chat sessions
- `GET /api/chat/sessions/{session_id}` - Get session details
- `DELETE /api/chat/sessions/{session_id}` - Delete a chat session

### Health
- `GET /api/health` - Check API health and configuration status

## Structure

- `app/main.py`: FastAPI app + CORS + routers
- `app/api/v1/*`: versioned endpoints (`/api` prefix already applied in main)
- `app/core/config.py`: settings (paths, CORS, API keys)
- `app/schemas/*`: Pydantic I/O contracts
- `app/services/*`: RAG service, LLM service, PDF processing, vector operations
- `app/repositories/*`: Database repository layer
- `app/db/*`: Database initialization and migrations
- `app/models/*`: SQLAlchemy models

## Environment

Create `backend/.env` by copying from `backend/.env.example`:

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` and fill in your values:

```env
# REQUIRED: Google Gemini API Key
# Get your API key from: https://ai.google.dev/ or https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional: Override model IDs (defaults shown)
CHAT_MODEL_ID=gemini-2.0-flash
TEXT_SUMMARIZER_MODEL_ID=gemini-2.0-flash
IMAGE_SUMMARIZER_MODEL_ID=gemini-2.0-flash

# Ollama Configuration (for embeddings)
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL_ID=embeddinggemma:latest

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///./data/app.db

# Logging (optional)
LOG_LEVEL=INFO
```

**Important:** Make sure Ollama is running and the embedding model is pulled:
```bash
ollama serve
ollama pull embeddinggemma:latest
```

## Frontend CORS

- Vite default: `http://localhost:5173`
- Update `app/core/config.py` if your port differs.
