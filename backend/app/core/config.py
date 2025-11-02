from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import List, Union
import os
from dotenv import load_dotenv

# Look for .env file in project root (one level up from backend/)
# Path: backend/app/core/config.py -> backend/ -> root/
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
_root_dir = os.path.dirname(_backend_dir)  # project root

# Check multiple locations in order of preference:
# 1. Project root .env (primary location)
# 2. /app/.env (Docker mount location - root .env mounted at backend level)
# 3. backend/.env (fallback for backward compatibility)
_env_file_path = None
for path in [
    os.path.join(_root_dir, ".env"),  # Project root
    "/app/.env",  # Docker mount location
    os.path.join(_backend_dir, ".env"),  # backend/.env fallback
]:
    if os.path.exists(path):
        _env_file_path = path
        break

if _env_file_path:
    load_dotenv(_env_file_path, override=True)


class Settings(BaseSettings):
    # pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=_env_file_path,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",  # Don't add any prefix
        case_sensitive=False,  # Case insensitive for env vars
    )
    api_v1_str: str = "/api"

    # CORS - defaults are set, can override via CORS_ALLOW_ORIGINS env var (comma-separated)
    cors_allow_origins: List[str] = Field(
        default=[
            "http://localhost:5173",  # Vite default & Docker frontend port
            "http://localhost:3000",
            "http://localhost:8080",  # Vite fallback
            "http://127.0.0.1:5173",  # Alternative localhost format
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://frontend:80",  # Docker internal frontend
        ]
    )
    
    @model_validator(mode="before")
    @classmethod
    def parse_cors_from_env(cls, data: Union[dict, type]) -> dict:
        """Parse CORS_ALLOW_ORIGINS from environment if provided as comma-separated string."""
        if isinstance(data, dict):
            cors_value = data.get("cors_allow_origins") or os.getenv("CORS_ALLOW_ORIGINS")
            if cors_value and isinstance(cors_value, str):
                # Split comma-separated string into list
                data["cors_allow_origins"] = [x.strip() for x in cors_value.split(",") if x.strip()]
        return data

    # Paths
    base_dir: str = Field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    data_dir: str = Field(default_factory=lambda: os.path.join(os.getcwd(), "data"))
    uploads_dir: str = Field(default_factory=lambda: os.path.join(os.getcwd(), "data", "uploads"))
    chroma_dir: str = Field(default_factory=lambda: os.path.join(os.getcwd(), "chroma_db"))

    # Ollama configuration
    ollama_base_url: str = "http://localhost:11434"

    # Google Gemini API configuration
    google_api_key: str = Field(default="")
    
    # Gemini model names (set in .env)
    chat_model_id: str = Field(default="gemini-2.0-flash")
    text_summarizer_model_id: str = Field(default="gemini-2.0-flash")
    image_summarizer_model_id: str = Field(default="gemini-2.0-flash")  # Vision-capable model
    
    # Ollama model names (for embedding only, kept for compatibility)
    embedding_model_id: str = "embeddinggemma:latest"

    # Concurrency knobs
    text_summarizer_max_workers: int = 4

    # Upload constraints
    max_upload_mb: int = 25
    allowed_mime_types: List[str] = ["application/pdf"]

    # (Inner Config not needed with model_config in pydantic v2)


settings = Settings()

# Debug: Log if API key is missing (only log first time to avoid spam)
if not settings.google_api_key:
    import logging
    logger = logging.getLogger(__name__)
    checked_paths = [
        os.path.join(_root_dir, ".env"),
        "/app/.env",
        os.path.join(_backend_dir, ".env"),
    ]
    logger.warning(
        f"GOOGLE_API_KEY is empty! "
        f"Checked .env files at: {checked_paths}. "
        f"Found .env at: {_env_file_path if _env_file_path else 'None'}. "
        f"Make sure GOOGLE_API_KEY is set in your .env file."
    )


