from fastapi import APIRouter

from . import health, documents, upload, chat


api_router_v1 = APIRouter()

api_router_v1.include_router(health.router, tags=["health"])
api_router_v1.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router_v1.include_router(upload.router, tags=["upload"])
api_router_v1.include_router(chat.router, tags=["chat"])


