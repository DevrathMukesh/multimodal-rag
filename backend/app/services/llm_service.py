"""Centralized LLM service for managing Google Gemini models."""
from typing import Optional
import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global LLM instances (singleton pattern)
_chat_llm: Optional[ChatGoogleGenerativeAI] = None
_text_summarizer_llm: Optional[ChatGoogleGenerativeAI] = None
_image_summarizer_llm: Optional[ChatGoogleGenerativeAI] = None


def _validate_api_key() -> None:
    """Validate that Google API key is configured."""
    if not settings.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Define it in your .env file. "
            "Make sure the .env file is in the backend directory and restart the server."
        )


def get_chat_llm() -> ChatGoogleGenerativeAI:
    """Get or create the chat LLM instance."""
    global _chat_llm
    if _chat_llm is None:
        _validate_api_key()
        _chat_llm = ChatGoogleGenerativeAI(
            model=settings.chat_model_id,
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )
    return _chat_llm


def get_chat_llm_streaming() -> ChatGoogleGenerativeAI:
    """Get a streaming-enabled chat LLM instance."""
    _validate_api_key()
    return ChatGoogleGenerativeAI(
        model=settings.chat_model_id,
        google_api_key=settings.google_api_key,
        temperature=0.7,
        streaming=True,
    )


def get_text_summarizer_llm() -> ChatGoogleGenerativeAI:
    """Get or create the text summarizer LLM instance."""
    global _text_summarizer_llm
    if _text_summarizer_llm is None:
        _validate_api_key()
        _text_summarizer_llm = ChatGoogleGenerativeAI(
            model=settings.text_summarizer_model_id,
            google_api_key=settings.google_api_key,
            temperature=0.3,
            max_tokens=512,
            max_retries=0,  # Disable LangChain's automatic retries - we handle rate limits ourselves
        )
    return _text_summarizer_llm


def get_image_summarizer_llm() -> ChatGoogleGenerativeAI:
    """Get or create the image summarizer LLM instance."""
    global _image_summarizer_llm
    if _image_summarizer_llm is None:
        _validate_api_key()
        _image_summarizer_llm = ChatGoogleGenerativeAI(
            model=settings.image_summarizer_model_id,
            google_api_key=settings.google_api_key,
            temperature=0.3,
            max_retries=0,  # Disable LangChain's automatic retries - we handle rate limits ourselves
        )
    return _image_summarizer_llm

