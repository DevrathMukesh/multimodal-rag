from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import logging
import random

from fastapi import HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import answer_question, build_prompt
from app.services.vector_service import retrieve_with_sources
from app.services.llm_service import get_chat_llm_streaming
from app.repositories.message_repo import get_messages_by_session, create_message
from app.repositories.session_repo import list_sessions, delete_session, get_session_summary
from app.api.v1.deps import get_db
from app.utils.rate_limit import is_rate_limit_error, extract_wait_seconds_from_error
import asyncio
import json


router = APIRouter()


def _load_conversation_history(db: Session, session_id: str, limit: int = 20) -> list[dict]:
    """Load conversation history for a session."""
    history_messages = get_messages_by_session(db, session_id, limit=limit)
    return [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
    ]


@router.get("/chat/messages/{session_id}")
async def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a session."""
    messages = get_messages_by_session(db, session_id)
    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "sources": msg.get_sources(),  # Include sources if available
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    # Load conversation history
    conversation_history = _load_conversation_history(db, req.sessionId)
    
    # Save user message
    create_message(db, session_id=req.sessionId, role="user", content=req.question)
    
    # Get answer
    result = answer_question(
        req.question,
        document_id=req.documentId,
        session_id=req.sessionId,
        conversation_history=conversation_history,
        include_images=req.includeImages if req.includeImages is not None else True,
    )
    
    # Save assistant response with sources
    create_message(
        db, 
        session_id=req.sessionId, 
        role="assistant", 
        content=result["answer"],
        sources=result["sources"]  # Save sources with the message
    )
    
    return ChatResponse(answer=result["answer"], sources=result["sources"])


@router.get("/chat/stream")
async def chat_stream(
    question: str, 
    sessionId: str, 
    documentId: str | None = None, 
    includeImages: bool = True,
    db: Session = Depends(get_db)
) -> EventSourceResponse:
    # Load conversation history
    conversation_history = _load_conversation_history(db, sessionId)
    
    # Save user message
    create_message(db, session_id=sessionId, role="user", content=question)
    
    bundle = retrieve_with_sources(
        query=question,
        k=5,
        document_id=documentId,
        include_images=includeImages,
    )
    parents = bundle.get("parents", [])
    prompt = build_prompt(question, parents, conversation_history=conversation_history, include_images=False)
    
    # Store response for saving later
    response_buffer = []

    async def event_generator() -> AsyncGenerator[str, None]:
        logger = logging.getLogger(__name__)
        max_retries = 3
        retry_count = 0
        
        try:
            while retry_count <= max_retries:
                try:
                    llm = get_chat_llm_streaming()
                    messages = prompt.format_messages()
                    async for chunk in llm.astream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            content = str(chunk.content)
                            response_buffer.append(content)
                            yield content
                    # Success - break out of retry loop
                    break
                except Exception as e:
                    if is_rate_limit_error(e) and retry_count < max_retries:
                        wait_time = extract_wait_seconds_from_error(e)
                        if wait_time is None:
                            wait_time = 60.0 * (1.5 ** retry_count)  # Exponential backoff
                        
                        # Add jitter (10-20%) to prevent synchronized retries
                        jitter_percent = random.uniform(0.1, 0.2)
                        jitter = wait_time * jitter_percent
                        total_wait = wait_time + jitter
                        
                        logger.warning(
                            f"⚠️  Rate limit detected in streaming chat! "
                            f"Gemini suggested: {wait_time:.1f}s | Jitter ({jitter_percent*100:.0f}%): +{jitter:.1f}s | "
                            f"Total wait: {total_wait:.1f}s | Retry attempt {retry_count + 1}/{max_retries + 1}"
                        )
                        
                        # Send a single rate limit notification to frontend (no countdown spam)
                        rate_limit_event = {
                            "wait_seconds": int(total_wait),
                            "retry_attempt": retry_count + 1,
                            "max_retries": max_retries + 1,
                            "type": "waiting",
                        }
                        yield f"event: rate_limit\ndata: {json.dumps(rate_limit_event)}\n\n"
                        
                        # Wait silently without sending countdown updates every second
                        logger.info(f"⏳ Waiting {total_wait:.1f}s silently before retry...")
                        await asyncio.sleep(total_wait)
                        
                        logger.info(
                            f"✅ Wait complete ({total_wait:.1f}s). Retrying streaming request now (attempt {retry_count + 2}/{max_retries + 1})..."
                        )
                        retry_count += 1
                        continue
                    else:
                        # Not a rate limit error or retries exhausted
                        logger.error(f"Error in chat stream: {str(e)}", exc_info=True)
                        error_msg = f"[ERROR: {str(e)}]"
                        response_buffer.append(error_msg)
                        yield error_msg
                        break
        finally:
            try:
                # Save assistant response to database with sources
                if response_buffer:
                    full_response = "".join(response_buffer)
                    if not full_response.startswith("[ERROR:"):
                        # Retrieve sources for this query to save with the message
                        sources = bundle.get("sources", [])
                        create_message(
                            db, 
                            session_id=sessionId, 
                            role="assistant", 
                            content=full_response,
                            sources=sources  # Save sources with the message
                        )
            except Exception as e:
                logger.error(f"Error saving message to database: {str(e)}", exc_info=True)
            finally:
                yield "event: end"

    return EventSourceResponse(event_generator())


@router.get("/chat/sessions")
async def get_chat_sessions(db: Session = Depends(get_db)):
    """Get all chat sessions with metadata."""
    sessions = list_sessions(db)
    return {"sessions": sessions}


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Get summary information for a specific session."""
    summary = get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    deleted = delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True, "message": "Session deleted successfully"}


