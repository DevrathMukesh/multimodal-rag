from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os
from dotenv import load_dotenv

# Explicitly load .env file as fallback - ensures it's loaded even if path resolution fails
_env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(_env_file_path):
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

    # CORS
    cors_allow_origins: List[str] = [
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
        "http://localhost:8080",  # Vite fallback (current dev server)
    ]

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
    logger.warning(
        f"GOOGLE_API_KEY is empty! "
        f"Checked .env file at: {_env_file_path}, "
        f"File exists: {os.path.exists(_env_file_path)}"
    )


