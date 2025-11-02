from fastapi import APIRouter
from app.core.config import settings


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "google_api_key_loaded": bool(settings.google_api_key),
        "google_api_key_length": len(settings.google_api_key) if settings.google_api_key else 0,
        "chat_model": settings.chat_model_id,
    }


