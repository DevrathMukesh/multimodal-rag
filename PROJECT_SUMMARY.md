# Multimodal RAG Project Summary

## Overview

Multimodal RAG system that processes PDFs (text, tables, images) and enables natural language querying with source citations. Uses Google Gemini for AI and Ollama for embeddings.

## Architecture

- **Backend**: FastAPI (Python) - document processing, vector storage, AI orchestration
- **Frontend**: React + TypeScript - document management and chat interface
- **Database**: SQLite (metadata), ChromaDB (vector embeddings)
- **Models**: 
  - Google Gemini 2.0 Flash (chat, summarization, vision)
  - Ollama EmbeddingGemma (local embeddings)

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, LangChain, Unstructured.io
- **Vector DB**: ChromaDB
- **Embeddings**: Ollama (local)
- **LLM**: Google Gemini API
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui

## Core Services

### PDF Service
- Extracts text, tables, images using Unstructured.io (`hi_res` strategy)
- Normalizes to JSON format (`parents.json`)

### Summary Service
- Generates summaries for text/table chunks and images (parallel processing)
- Uses Gemini with special handling for title pages

### Vector Service
- Indexes summaries in ChromaDB with Ollama embeddings
- Multi-vector approach: summaries (children) → original content (parents)
- Parent index mapping for retrieval

### RAG Service
- Orchestrates query → retrieval → answer generation
- Combines vector search results with conversation history

### LLM Service
- Manages Gemini models: Chat (temp=0.7), Summarizer (temp=0.3), Vision (temp=0.3)

## Data Flow

1. **Upload**: PDF → Extract (text/tables/images) → Summarize → Embed → Store in ChromaDB
2. **Query**: Question → Embed → Vector search → Retrieve context → Generate answer with sources

## Features

- PDF upload with progress tracking (background processing with status endpoint)
- Multimodal extraction (text, tables, images)
- Semantic search with source citations
- Streaming chat responses (SSE with rate limit handling)
- Non-streaming chat endpoint for simple queries
- Conversation history and session management
- Intelligent rate limit handling with:
  - Automatic retry mechanism (up to 4 attempts)
  - Wait time extraction from API error messages
  - Exponential backoff with jitter
  - User-friendly countdown notifications
  - Graceful error handling
- Real-time progress updates during document processing
- Document status tracking (processing, completed, failed)

## API Endpoints

### Document Management
- `POST /api/upload` - Upload PDF (returns immediately, processes in background)
- `GET /api/upload/status/{doc_id}` - Get upload processing status and progress
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{id}` - Delete document and associated data

### Chat
- `POST /api/chat` - Chat (non-streaming, returns complete response)
- `GET /api/chat/stream` - Chat (streaming SSE with rate limit handling)
- `GET /api/chat/messages/{session_id}` - Get chat history for a session
- `GET /api/chat/sessions` - List all chat sessions
- `GET /api/chat/sessions/{session_id}` - Get session summary information
- `DELETE /api/chat/sessions/{id}` - Delete session and all messages

### Health
- `GET /api/health` - API health check

## Configuration

Required `.env` (project root):
```env
GOOGLE_API_KEY=your_key
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL_ID=embeddinggemma:latest
CHAT_MODEL_ID=gemini-2.0-flash
TEXT_SUMMARIZER_MODEL_ID=gemini-2.0-flash
IMAGE_SUMMARIZER_MODEL_ID=gemini-2.0-flash
```

## Data Storage

- `backend/data/app.db` - SQLite (documents, messages, sessions metadata)
- `backend/data/uploads/{doc_id}/` - PDF files and processed JSON
  - `parents.json` - Extracted content (texts, tables, images)
  - `summaries.json` - Generated summaries
- `backend/chroma_db/` - ChromaDB vector store (vector embeddings)
- `backend/data/parents_index/{doc_id}.json` - Parent-child mappings for retrieval
- `backend/data/logs/` - Application logs

## Quick Start

```bash
# Docker (recommended)
docker-compose up -d

# Local
# 1. Install dependencies (see README.md)
# 2. Start Ollama: ollama serve
# 3. Pull model: ollama pull embeddinggemma:latest
# 4. Start backend: cd backend && uvicorn app.main:app --reload
# 5. Start frontend: cd frontend && npm run dev
```

## Fresh Start

The `fresh_start.py` script provides an automated way to reset the application:

```bash
python3 fresh_start.py  # Interactive cleanup script
```

**What it deletes:**
- SQLite database (`app.db`)
- All uploaded documents and processed files
- ChromaDB vector store
- Parents index mappings
- Application logs

**Features:**
- Supports both local and Docker environments
- Interactive confirmation prompts
- Safe deletion with size reporting
- Option to restart Docker containers automatically

**Note:** This action is irreversible. All data will be permanently deleted.
