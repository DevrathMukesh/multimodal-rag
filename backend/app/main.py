from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

# Disable ChromaDB telemetry to avoid connection warnings
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from app.core.config import settings
from app.api.v1.router import api_router_v1
from app.db.init_db import init_db, init_directories
from app.core.logging import setup_logging
from app.services.llm_service import get_text_summarizer_llm, get_image_summarizer_llm, get_chat_llm
import logging
import httpx
import subprocess
import time
import shutil
import sys


def create_app() -> FastAPI:
    app = FastAPI(title="Multimodal RAG Backend", version="0.1.0")

    # CORS configuration
    cors_origins = ["*"] if settings.cors_allow_all else settings.cors_allow_origins
    if settings.cors_allow_all:
        logging.info("CORS: Allowing all origins (*)")
    else:
        logging.info("CORS: Allowing origins: %s", cors_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.include_router(api_router_v1, prefix="/api")

    return app


app = create_app()

def check_ollama_connection() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            logging.info("✓ Ollama server is running and accessible at %s", settings.ollama_base_url)
            return True
        logging.warning("Ollama server returned status %d", response.status_code)
        return False
    except httpx.ConnectError:
        return False
    except Exception as e:
        logging.warning("Error checking Ollama connection: %s", e)
        return False


def start_ollama_server() -> bool:
    """Attempt to automatically start Ollama server."""
    # Check if ollama command exists
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        logging.error("✗ 'ollama' command not found in PATH. Please install Ollama first.")
        return False
    
    logging.info("🔄 Attempting to start Ollama server...")
    
    try:
        # Start Ollama in background
        # On Unix-like systems, use start_new_session to detach from parent
        if sys.platform != "win32":
            process = subprocess.Popen(
                [ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        else:
            # Windows
            process = subprocess.Popen(
                [ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        
        # Give it a few seconds to start up
        logging.info("⏳ Waiting for Ollama server to start...")
        for i in range(10):  # Check for up to 10 seconds
            time.sleep(1)
            if check_ollama_connection():
                logging.info("✓ Ollama server started successfully!")
                return True
            if i < 9:
                logging.debug(f"Still waiting... ({i+1}/10)")
        
        logging.warning("⚠ Ollama process started but server not responding yet")
        return False
        
    except Exception as e:
        logging.error(f"✗ Failed to start Ollama server: {e}")
        return False


# Initialize storage and database on startup
@app.on_event("startup")
def on_startup() -> None:
    setup_logging()
    init_directories()
    init_db()

    # Display configuration
    logging.info("\n" + "="*70)
    logging.info("CONFIGURATION")
    logging.info("="*70)
    logging.info("CORS Origins: %s", settings.cors_allow_origins)
    logging.info("="*70 + "\n")
    
    # Display embedding provider configuration
    logging.info("EMBEDDING PROVIDER CONFIGURATION")
    logging.info("="*70)
    
    if settings.use_ollama_embeddings:
        logging.info("🔧 Provider: OLLAMA (Local Embeddings)")
        logging.info("   Model: %s", settings.embedding_model_id)
        logging.info("   URL: %s", settings.ollama_base_url)
        logging.info("   Mode: MULTIMODAL (Text + Tables + Images)")
        
        # Check Ollama connection first, auto-start if not running
        ollama_available = check_ollama_connection()
        if not ollama_available:
            logging.info("Ollama server is not running. Attempting to start automatically...")
            ollama_available = start_ollama_server()
            
            if not ollama_available:
                logging.error(
                    "\n" + "="*70 + "\n"
                    "WARNING: Could not start Ollama server automatically!\n"
                    "Please start Ollama manually by running: ollama serve\n"
                    "Or ensure Ollama is installed and available in your PATH.\n"
                    "The application will continue but model operations will fail.\n"
                    + "="*70 + "\n"
                )
            else:
                logging.info("✓ Ollama server is ready")
        else:
            logging.info("✓ Ollama server is ready")
    else:
        logging.info("🔧 Provider: GOOGLE GEMINI API (Serverless Embeddings)")
        logging.info("   Model: %s", settings.embedding_api_model_id)
        logging.info("   Mode: TEXT-ONLY (Text + Tables, Images disabled)")
        if settings.google_api_key:
            logging.info("   API Key: ✓ Set")
        else:
            logging.warning("   API Key: ✗ NOT SET - Embedding operations will fail!")
    
    logging.info("="*70 + "\n")

    # Display LLM models configuration
    logging.info("LLM MODELS CONFIGURATION")
    logging.info("="*70)
    logging.info("   Chat Model: %s", settings.chat_model_id)
    logging.info("   Text Summarizer: %s", settings.text_summarizer_model_id)
    if settings.use_ollama_embeddings:
        logging.info("   Image Summarizer: %s", settings.image_summarizer_model_id)
    else:
        logging.info("   Image Summarizer: DISABLED (text-only mode)")
    logging.info("="*70 + "\n")

    # Warm-up LLM models to avoid first-request latency
    try:
        get_text_summarizer_llm()
        logging.info("✓ Text summarizer model warm-up successful")
    except Exception as e:
        logging.warning("Text summarizer model warm-up failed: %s", e)
    
    if settings.use_ollama_embeddings:
        try:
            get_image_summarizer_llm()
            logging.info("✓ Image summarizer model warm-up successful")
        except Exception as e:
            logging.warning("Image summarizer model warm-up failed: %s", e)
    else:
        logging.info("⏭️  Image summarizer warm-up skipped (text-only mode)")
    
    try:
        get_chat_llm()
        logging.info("✓ Chat model warm-up successful")
    except Exception as e:
        logging.warning("Chat model warm-up failed: %s", e)
    
    logging.info("\n" + "="*70)
    logging.info("🚀 Application startup complete!")
    logging.info("="*70 + "\n")


