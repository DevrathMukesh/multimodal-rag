# Multimodal RAG System

A powerful **Multimodal Retrieval-Augmented Generation (RAG)** system that enables intelligent querying of PDF documents with support for text, tables, and images. Built with FastAPI backend and React frontend.

![Multimodal RAG](https://img.shields.io/badge/Multimodal-RAG-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-green)
![React](https://img.shields.io/badge/React-18.3.1-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-blue)

## 🎯 Overview

This system processes PDF documents to extract text, tables, and images, generates intelligent summaries using Google Gemini AI, and provides natural language question-answering with source citations. It uses vector search (ChromaDB with Ollama embeddings) for semantic retrieval and Google Gemini for conversational AI.

## ✨ Key Features

- **📄 PDF Processing**: Extracts text, tables, and images from PDF documents
- **🤖 AI-Powered Summarization**: Generates intelligent summaries using Google Gemini
- **🔍 Semantic Search**: Vector-based retrieval using ChromaDB and Ollama embeddings
- **💬 Conversational AI**: Natural language Q&A with context-aware responses
- **📊 Source Citations**: Answers include page references with relevance scores
- **🌊 Streaming Responses**: Real-time token-by-token streaming via Server-Sent Events
- **💾 Persistent Sessions**: Chat history and conversation context management
- **🎨 Modern UI**: React-based interface with dark/light theme support

## 🎬 Demo
Here’s a short walkthrough of the **Multimodal RAG System** in action — showcasing document upload, intelligent summarization, and natural language Q&A.
### 🔗 **Demo Video:**  

[Watch Demo Video](https://private-user-images.githubusercontent.com/95998192/517765585-b40bd6d5-a1a2-44a5-8159-6135f8cf271d.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM4NDcyMzMsIm5iZiI6MTc2Mzg0NjkzMywicGF0aCI6Ii85NTk5ODE5Mi81MTc3NjU1ODUtYjQwYmQ2ZDUtYTFhMi00NGE1LTgxNTktNjEzNWY4Y2YyNzFkLm1wND9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTIyVDIxMjg1M1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTEyNzcyMmNiMjRhYWVhMWU4YzA5MGJhYzEyZThhNWIwMGM5NWJlMjAzZjUwZjZjMzcyNTVjNDU5MTUxMjQwM2QmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.Nve4IIWcLrP02STTQGO9gBQ1Q6c-kVjl79eWlP1TYmQ)


<p align="center">
  <img width="85%" alt="Multimodal RAG Demo" src="https://github.com/user-attachments/assets/51aa163e-408a-4fb5-aeb5-57ce06c2e473" />
</p>
Above: A snapshot of the rate-limiting feature in action, showing how the system gracefully handles API quota limits with countdown and retry feedback.

When API rate limits are exceeded, the system automatically:
- Displays a user-friendly notification with countdown timer
- Implements automatic retry mechanism (up to 4 attempts)
- Pauses chat interactions until the limit resets
- Provides real-time feedback on retry attempts

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend  │ (TypeScript, shadcn/ui, Tailwind CSS)
└────────┬────────┘
         │ REST API / SSE
┌────────▼──────────────────────────┐
│      FastAPI Backend              │
│  ┌─────────────────────────────┐  │
│  │  PDF Service                │  │ (Unstructured.io)
│  │  Summary Service            │  │ (Google Gemini)
│  │  Vector Service             │  │ (ChromaDB + Ollama)
│  │  RAG Service                │  │ (Orchestration)
│  │  LLM Service                │  │ (Google Gemini)
│  └─────────────────────────────┘  │
└────────┬──────────────────────────┘
         │
    ┌────┴────┐
    │ SQLite  │ (Metadata)
    │ ChromaDB│ (Vectors)
    └─────────┘
```

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

The easiest way to run the entire system with all dependencies:

1. **Prerequisites**
   - Docker Engine 20.10+
   - Docker Compose 2.0+
   - Google Gemini API Key

2. **Setup Environment**
   
   Create `.env` file in the project root:
   ```bash
   # Copy environment file to root
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```
   
   **Note**: The backend looks for `.env` in the project root first, then falls back to `backend/.env` if root `.env` doesn't exist (for backward compatibility).

3. **Start Everything**
   
   Start Docker containers based on your `.env` setting:
   
   **With Ollama (Multimodal - Default):**
   ```bash
   # If USE_OLLAMA_EMBEDDINGS=true in .env
   docker-compose --profile ollama up -d
   ```
   - Ollama container starts
   - Model downloads (~621 MB on first run, takes 2-5 minutes)
   - Supports: text + tables + images
   
   **Without Ollama (Text-Only - Serverless):**
   ```bash
   # If USE_OLLAMA_EMBEDDINGS=false in .env
   docker-compose up -d
   ```
   - Ollama container does NOT start (saves resources!)
   - No model download
   - Uses Google Gemini API embeddings
   - Supports: text + tables only
   
   **Development Mode (with hot reload):**
   ```bash
   # With Ollama
   docker-compose --profile dev --profile ollama up -d
   
   # Without Ollama
   docker-compose --profile dev up -d
   ```
   
   **Note:** 
   - When `USE_OLLAMA_EMBEDDINGS=true`, the first startup downloads the embedding model (~621 MB)
   - Monitor progress: `docker logs multimodal-rag-ollama-init`
   - Model is cached in `ollama-data` volume for faster subsequent startups
   - When `USE_OLLAMA_EMBEDDINGS=false`, Ollama doesn't start at all, saving resources

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Ollama: http://localhost:11434

### Option 2: Local Development 💻

For development without Docker (requires manual installation of system dependencies):

**📖 See [SETUP_LOCAL.md](./SETUP_LOCAL.md) for complete platform-specific instructions (macOS, Linux, Windows).**

1. **Prerequisites**
   - **Python 3.11+**
   - **Node.js & npm** (for frontend)
   - **Ollama** installed and running
   - **Google Gemini API Key** ([Get one here](https://ai.google.dev/))

2. **Setup Ollama**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama serve
   ollama pull embeddinggemma:latest
   ```

3. **Backend Setup**

   **Install System Dependencies** (required for PDF processing):
   
   **macOS:**
   ```bash
   brew install poppler tesseract libmagic
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install poppler-utils tesseract-ocr libmagic-dev
   ```
   
   **Windows:**
   ```bash
   # Using Chocolatey (install from https://chocolatey.org/)
   choco install poppler tesseract libmagic
   
   # OR using winget
   winget install poppler tesseract-ocr libmagic
   ```
   
   **Then install Python dependencies:**
   ```bash
   cd backend
   
   # Using conda (recommended for this project)
   conda activate rag  # Or create: conda create -n rag python=3.11
   pip install -r requirements.txt
   
   # OR using Poetry (for dependency resolution only)
   poetry install --no-root
   # Note: Poetry is used for dependency resolution, but runtime uses conda
   
   # OR using pip with virtualenv
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   
   # Configure environment
   # Create .env in project root (not backend/.env)
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY and configure other settings
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

5. **Running the Application**
   ```bash
   # Terminal 1: Start Backend
   cd backend
   conda activate rag
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # OR using Poetry (if not using conda)
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Start Frontend
   cd frontend
   npm run dev
   ```

6. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📖 Usage

1. **Upload Documents**
   - Navigate to the upload page or use the document sidebar
   - Drag and drop or select a PDF file
   - Wait for processing to complete (extraction, summarization, indexing)

2. **Chat with Documents**
   - Select a document (optional) or chat across all documents
   - Type your question in the chat interface
   - Receive answers with source citations showing:
     - Page numbers
     - Content previews
     - Relevance scores
     - Image thumbnails (if applicable)

3. **Manage Sessions**
   - Create new chat sessions
   - View conversation history
   - Delete old sessions

## 🐳 Docker Quick Commands

```bash
# Start services (production)
docker-compose up -d

# Start services (development with hot reload)
docker-compose --profile dev up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Rebuild specific service
docker-compose build --no-cache backend

# Initialize Ollama model (required after first start)
docker exec -it multimodal-rag-ollama ollama pull embeddinggemma:latest

# Check service status
docker-compose ps

# Access container shell
docker exec -it multimodal-rag-backend bash
docker exec -it multimodal-rag-frontend sh
```

## 🔧 Configuration

### Backend Environment Variables

Create `.env` file in the project root (copy from `.env.example`):

```env
# ============================================================================
# Google Gemini API Configuration
# ============================================================================
GOOGLE_API_KEY=your_google_gemini_api_key_here
CHAT_MODEL_ID=gemini-2.0-flash
TEXT_SUMMARIZER_MODEL_ID=gemini-2.0-flash
IMAGE_SUMMARIZER_MODEL_ID=gemini-2.0-flash
EMBEDDING_API_MODEL_ID=models/text-embedding-004

# ============================================================================
# Ollama Configuration (Local Embeddings)
# ============================================================================
# Set USE_OLLAMA_EMBEDDINGS=true to use local Ollama embeddings
# When false, uses Google Gemini API embeddings (text-only mode for serverless)
USE_OLLAMA_EMBEDDINGS=true
OLLAMA_BASE_URL=http://localhost:11434  # For Docker: http://ollama:11434
EMBEDDING_MODEL_ID=embeddinggemma:latest

# ============================================================================
# CORS Configuration
# ============================================================================
# Set CORS_ALLOW_ALL=true to allow all origins (recommended for development)
CORS_ALLOW_ALL=true

# ============================================================================
# Performance & Limits
# ============================================================================
TEXT_SUMMARIZER_MAX_WORKERS=4
MAX_UPLOAD_MB=25
```

**Key Configuration Options:**

- **`USE_OLLAMA_EMBEDDINGS`**: 
  - `true` (default): Use local Ollama embeddings (multimodal: text + tables + images)
  - `false`: Use Google Gemini API embeddings (text-only mode, suitable for serverless deployment)

- **`CORS_ALLOW_ALL`**: 
  - `true` (recommended for development): Allows all origins
  - `false`: Uses default allowed origins (localhost:5173, localhost:3000, etc.)

### Frontend Configuration

Create `frontend/.env.local` (optional):

```env
VITE_API_BASE=http://localhost:8000
```

## 📁 Project Structure

```
Multimodal RAG/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints (chat, documents, upload, health)
│   │   ├── core/            # Configuration and logging
│   │   ├── db/              # Database setup and migrations
│   │   ├── models/          # SQLAlchemy models (document, message)
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic (PDF, RAG, vector, summary, LLM)
│   │   └── utils/           # Utilities (file handling, rate limiting)
│   ├── chroma_db/           # Vector database storage
│   ├── data/                # SQLite DB, uploads, logs, parents_index
│   ├── reference code/      # Jupyter notebooks for experimentation
│   └── main.py              # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components (Chat, Sidebar, Upload, etc.)
│   │   ├── pages/           # Page components (ChatPage, UploadPage, etc.)
│   │   ├── lib/             # API client and utilities
│   │   └── types/           # TypeScript types
│   └── package.json
├── demo/                    # Demo video and screenshots
├── scripts/                 # Init scripts for Ollama
├── docker-compose.yml       # Docker orchestration
├── fresh_start.py          # Cleanup script
└── README.md                # This file
```

## 🔌 API Endpoints

### Document Management
- `POST /api/upload` - Upload and process PDF
- `GET /api/upload/status/{doc_id}` - Get upload processing status
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{doc_id}` - Delete document

### Chat
- `POST /api/chat` - Send chat message (non-streaming)
- `GET /api/chat/stream` - Stream chat responses (SSE)
- `GET /api/chat/messages/{session_id}` - Get chat history for a session
- `GET /api/chat/sessions` - List all chat sessions
- `GET /api/chat/sessions/{session_id}` - Get session summary information
- `DELETE /api/chat/sessions/{session_id}` - Delete session

### Health
- `GET /api/health` - API health check

See [backend/README.md](./backend/README.md) for detailed API documentation.

## 🤖 Models Used

- **Google Gemini 2.0 Flash**: Chat, text summarization, and image analysis
- **Ollama EmbeddingGemma**: Local embeddings for semantic search (when `USE_OLLAMA_EMBEDDINGS=true`)
- **Google Gemini Text Embedding 004**: API-based embeddings (when `USE_OLLAMA_EMBEDDINGS=false`)

**Embedding Provider Toggle:**
- Set `USE_OLLAMA_EMBEDDINGS=true` for local multimodal processing (text + tables + images)
- Set `USE_OLLAMA_EMBEDDINGS=false` for serverless deployment (text-only mode)

## 🛠️ Technology Stack

### Backend
- FastAPI - Web framework
- LangChain - AI orchestration
- ChromaDB - Vector database
- SQLAlchemy - ORM
- Unstructured.io - PDF processing
- Ollama - Local embeddings
- Google Gemini - LLM

### Frontend
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- shadcn/ui - UI components
- Tailwind CSS - Styling
- TanStack Query - Data fetching
- React Router - Routing

## 📚 Documentation

- **[SETUP_LOCAL.md](./SETUP_LOCAL.md)** - Complete local setup guide (without Docker) with platform-specific instructions
- **[Backend README](./backend/README.md)** - Detailed backend documentation
- **[Frontend README](./frontend/README.md)** - Frontend setup and usage
- **[Project Summary](./PROJECT_SUMMARY.md)** - Comprehensive technical overview

## 🧪 Development

### Backend Development
```bash
cd backend
conda activate rag
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR using Poetry
poetry run uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Running Tests
```bash
# Backend tests (if available)
cd backend
pytest

# Frontend tests (if available)
cd frontend
npm test
```

## 📝 Workflow

1. **Document Upload** → PDF extraction → Summarization → Vector indexing
2. **User Query** → Vector search → Context retrieval → Answer generation
3. **Response** → Streaming → Source attachment → Display

See [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) for detailed workflow explanation.

## 🔒 Security Notes

- Never commit `.env` files (they're in `.gitignore`)
- Store API keys in environment variables only
- Use HTTPS in production
- Validate file uploads (size, type)
- Keep Docker images updated for security patches

## 🐛 Troubleshooting

### Docker Issues

**Ollama not connecting:**
```bash
# Check if Ollama is running
docker-compose ps ollama

# Check Ollama logs
docker-compose logs ollama

# Verify model is pulled
docker exec -it multimodal-rag-ollama ollama list
```

**Backend can't connect to Ollama:**
- In Docker, backend automatically uses `http://ollama:11434`
- For local dev, ensure Ollama is running on `http://localhost:11434`

**Port conflicts:**
- Change ports in `docker-compose.yml` if 8000, 5173, or 11434 are in use

**Permission issues:**
```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) backend/data backend/chroma_db
```

**Out of memory:**
- Ollama and PyTorch can use significant RAM
- Minimum 4GB RAM required
- Increase Docker Desktop memory limits if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- Ollama for local embeddings
- Unstructured.io for PDF processing
- LangChain for AI orchestration
- shadcn/ui for UI components

## 📞 Support

For issues and questions:
- Check the documentation in `PROJECT_SUMMARY.md`
- Review backend/frontend README files
- Check Docker logs: `docker-compose logs -f`
- Open an issue on the repository

---

**Made with ❤️ for intelligent document Q&A**
