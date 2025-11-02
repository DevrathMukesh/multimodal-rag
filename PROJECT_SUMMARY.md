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

- PDF upload with progress tracking (SSE)
- Multimodal extraction (text, tables, images)
- Semantic search with source citations
- Streaming chat responses (SSE)
- Conversation history and session management
- Rate limit handling with automatic retries
- Real-time progress updates during processing

## API Endpoints

- `POST /api/upload` - Upload PDF (SSE progress stream)
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/chat` - Chat (non-streaming)
- `GET /api/chat/stream` - Chat (streaming SSE)
- `GET /api/chat/messages/{session_id}` - Get history
- `GET /api/chat/sessions` - List sessions
- `DELETE /api/chat/sessions/{id}` - Delete session

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

- `backend/data/app.db` - SQLite (documents, messages, sessions)
- `backend/data/uploads/{doc_id}/` - PDF files and processed JSON
- `backend/chroma_db/` - ChromaDB vector store
- `backend/data/parents_index/{doc_id}.json` - Parent-child mappings

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

```bash
python3 fresh_start.py  # Automated cleanup script
```

Deletes: database, uploads, ChromaDB, parents_index, logs
