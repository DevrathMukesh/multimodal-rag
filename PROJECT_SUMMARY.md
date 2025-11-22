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

## Libraries and Their Purposes

### Backend Libraries

#### Core Framework & Web
- **FastAPI (0.115.4)**: Web framework for building REST API endpoints
- **Uvicorn (0.32.0)**: ASGI server for running FastAPI application
- **python-multipart (0.0.9)**: Handle file uploads (PDF files)

#### Data & Database
- **SQLAlchemy (2.0.35)**: ORM for managing SQLite database (documents, messages, sessions)
- **ChromaDB (0.5.23)**: Vector database for storing and querying embeddings
- **pypdf (5.0.1)**: PDF manipulation library (reading page count)

#### AI & ML Libraries
- **LangChain (0.3.7)**: Core framework for LLM orchestration and chains
- **langchain-community (0.3.7)**: Community integrations for LangChain
- **langchain-ollama**: Ollama integration for local embeddings
- **langchain-chroma**: ChromaDB integration for vector store
- **langchain-google-genai**: Google Gemini integration for chat and summarization
- **transformers**: Hugging Face transformers (for embeddings if needed)
- **torch**: PyTorch (ML framework, used by transformers)
- **sentence-transformers**: Sentence embedding models
- **accelerate**: Hugging Face acceleration library
- **safetensors**: Safe tensor serialization
- **tiktoken (0.8.0)**: Token counting for text chunks

#### PDF Processing
- **unstructured (>=0.16.11,<0.17.0)**: PDF parsing and extraction (text, tables, images)
- **unstructured_inference**: ML models for document understanding
- **pdf2image**: Convert PDF pages to images
- **pdfminer.six (20221105)**: PDF text extraction backend
- **pi-heif**: HEIF image format support
- **Pillow (11.0.0)**: Image processing and manipulation

#### Configuration & Utilities
- **pydantic (2.9.2)**: Data validation and settings management
- **pydantic-settings (2.6.1)**: Settings management from environment variables
- **python-dotenv (1.0.1)**: Load environment variables from `.env` files
- **sse-starlette (2.1.3)**: Server-Sent Events for streaming responses

#### OpenAI (Optional)
- **openai (^1.54.0)**: OpenAI API client (if needed for alternative models)

### Frontend Libraries

#### Core Framework
- **React (^18.3.1)**: UI framework
- **React DOM (^18.3.1)**: React rendering
- **TypeScript (^5.8.3)**: Type-safe JavaScript

#### Routing & State
- **react-router-dom (^6.30.1)**: Client-side routing
- **@tanstack/react-query (^5.83.0)**: Data fetching and caching

#### UI Components
- **shadcn/ui** (via Radix UI primitives):
  - `@radix-ui/react-*`: Accessible UI primitives (dialogs, dropdowns, tabs, etc.)
- **lucide-react (^0.462.0)**: Icon library
- **react-markdown (^10.1.0)**: Markdown rendering
- **remark-gfm (^4.0.1)**: GitHub Flavored Markdown support

#### Forms & Validation
- **react-hook-form (^7.61.1)**: Form state management
- **@hookform/resolvers (^3.10.0)**: Form validation resolvers
- **zod (^3.25.76)**: Schema validation

#### Styling
- **Tailwind CSS (^3.4.17)**: Utility-first CSS framework
- **tailwindcss-animate (^1.0.7)**: Animation utilities
- **@tailwindcss/typography (^0.5.16)**: Typography plugin
- **tailwind-merge (^2.6.0)**: Merge Tailwind classes
- **clsx (^2.1.1)**: Conditional class names
- **class-variance-authority (^0.7.1)**: Component variants

#### Utilities
- **next-themes (^0.3.0)**: Dark/light theme switching
- **date-fns (^3.6.0)**: Date formatting
- **react-dropzone (^14.3.8)**: File drag-and-drop
- **sonner (^1.7.4)**: Toast notifications

#### Build Tools
- **Vite (^5.4.19)**: Build tool and dev server
- **@vitejs/plugin-react-swc (^3.11.0)**: Fast React refresh
- **ESLint**: Code linting
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixing

## Models and Their Usage

### Google Gemini Models

#### 1. **gemini-2.0-flash** (Chat Model)
- **Purpose**: Conversational AI and question answering
- **Usage**: Main chat interface for user queries
- **Configuration**: 
  - Temperature: `0.7` (balanced creativity/accuracy)
  - Used in: `llm_service.get_chat_llm()`, `rag_service.answer_question()`
- **Features**: Streaming support for real-time responses

#### 2. **gemini-2.0-flash** (Text Summarizer)
- **Purpose**: Summarize text and table content from PDFs
- **Usage**: Generate concise summaries of document chunks
- **Configuration**:
  - Temperature: `0.3` (more focused, factual)
  - Used in: `summary_service.summarize_texts()`
- **Features**: Special handling for title pages (preserves metadata)

#### 3. **gemini-2.0-flash** (Image Summarizer)
- **Purpose**: Analyze and describe images extracted from PDFs
- **Usage**: Generate text descriptions of images for vector search
- **Configuration**:
  - Temperature: `0.3` (accurate descriptions)
  - Used in: `summary_service.summarize_images()`
- **Features**: Vision capabilities, processes images sequentially to avoid rate limits

### Ollama Models

#### 1. **embeddinggemma:latest** (Embedding Model)
- **Purpose**: Generate vector embeddings for semantic search
- **Usage**: Embed summaries and query text for ChromaDB
- **Configuration**: Local model via Ollama API
- **Features**: 
  - Runs locally (no external API costs)
  - ~621MB model size
  - Used in: `vector_service` for indexing and retrieval

## LangChain Components Used

### LangChain Core (`langchain_core`)

#### 1. **ChatPromptTemplate**
- **Purpose**: Build structured prompts for LLMs
- **Usage**: 
  - `summary_service.py`: Create prompts for text/image summarization
  - `rag_service.py`: Build RAG prompts with context and conversation history
- **Features**: Template-based prompt construction with variable substitution

#### 2. **HumanMessage**
- **Purpose**: Represent user messages in chat format
- **Usage**: 
  - `summary_service.py`: Send content to Gemini for summarization
  - `rag_service.py`: Format user questions with context
- **Features**: Part of LangChain message system

#### 3. **StrOutputParser**
- **Purpose**: Parse LLM output as plain text
- **Usage**: Extract text from LLM responses (summaries, answers)
- **Features**: Simple string extraction from structured LLM responses

#### 4. **Document**
- **Purpose**: Standard document format for LangChain
- **Usage**: `vector_service.py` - Convert data to LangChain Document format for ChromaDB

### LangChain Integrations

#### 1. **ChatGoogleGenerativeAI** (`langchain_google_genai`)
- **Purpose**: Google Gemini LLM integration
- **Usage**: 
  - Chat: `llm_service.get_chat_llm()`, `get_chat_llm_streaming()`
  - Summarization: `llm_service.get_text_summarizer_llm()`, `get_image_summarizer_llm()`
- **Features**: 
  - Streaming support (`astream()`)
  - Temperature control
  - Vision capabilities for images

#### 2. **OllamaEmbeddings** (`langchain_ollama`)
- **Purpose**: Generate embeddings using Ollama models
- **Usage**: `vector_service.py` - Create embeddings for summaries and queries
- **Configuration**: Connects to local Ollama instance
- **Features**: Local embedding generation

#### 3. **Chroma** (`langchain_chroma`)
- **Purpose**: ChromaDB vector store integration
- **Usage**: `vector_service.py` - Store and retrieve embeddings
- **Features**:
  - Multi-vector indexing (children summaries → parent content)
  - Similarity search with metadata filtering
  - Document retrieval with sources

### LangChain Patterns Used

#### 1. **Chain Composition** (`prompt | llm | parser`)
- **Pattern**: `ChatPromptTemplate | LLM | StrOutputParser`
- **Usage**: 
  - Summary generation chains
  - RAG answer generation chains
- **Benefits**: Modular, composable, easy to test

#### 2. **Retrieval-Augmented Generation (RAG)**
- **Flow**: Query → Embed → Vector Search → Retrieve Context → Generate Answer
- **Implementation**: `rag_service.py` orchestrates the full RAG pipeline
- **Features**: 
  - Context injection from retrieved documents
  - Conversation history integration
  - Source citation generation

#### 3. **Multi-Vector Retrieval**
- **Pattern**: Store summaries (children) for search, retrieve original content (parents)
- **Implementation**: `vector_service.py` uses parent-child mapping
- **Benefits**: 
  - Better search with summaries
  - Full context retrieval from original content
  - Efficient storage and retrieval

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
