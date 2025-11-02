# Multimodal RAG Backend

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

## Structure

- `app/main.py`: FastAPI app + CORS + routers
- `app/api/v1/*`: versioned endpoints (`/api` prefix already applied in main)
- `app/core/config.py`: settings (paths, CORS, API keys)
- `app/schemas/*`: Pydantic I/O contracts
- `services`, `repositories`, and `db` will be filled next

## Environment

Create `backend/.env` with these keys (required for current setup):

```env
# Hugging Face (optional for gated models; enables first-time downloads)
HUGGINGFACEHUB_API_TOKEN=

# Local HF model ids (override defaults if desired)
CHAT_MODEL_ID=Qwen/Qwen2.5-7B-Instruct-AWQ
TEXT_SUMMARIZER_MODEL_ID=Qwen/Qwen2.5-3B-Instruct
IMAGE_SUMMARIZER_MODEL_ID=Qwen/Qwen2.5-VL-3B-Instruct-AWQ
EMBEDDING_MODEL_ID=Qwen/Qwen3-Embedding-0.6B

# OpenRouter (optional; only used if you switch chat/streaming back)
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Logging
LOG_LEVEL=INFO
```

## Frontend CORS

- Vite default: `http://localhost:5173`
- Update `app/core/config.py` if your port differs.
