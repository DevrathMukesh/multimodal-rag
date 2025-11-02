"""Repository for managing chat sessions."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime

from app.models.message import Message


def list_sessions(db: Session, limit: Optional[int] = None) -> List[dict]:
    """List all chat sessions with metadata."""
    # Get unique session IDs with their latest message timestamp
    query = (
        db.query(
            Message.session_id,
            func.max(Message.created_at).label("last_activity"),
            func.count(Message.id).label("message_count"),
            func.min(Message.created_at).label("created_at"),
        )
        .group_by(Message.session_id)
        .order_by(func.max(Message.created_at).desc())
    )
    
    if limit:
        query = query.limit(limit)
    
    sessions = query.all()
    
    # Get first user message for each session as title
    result = []
    for session_id, last_activity, message_count, created_at in sessions:
        first_message = (
            db.query(Message)
            .filter(Message.session_id == session_id, Message.role == "user")
            .order_by(Message.created_at.asc())
            .first()
        )
        
        title = first_message.content[:50] + "..." if first_message and len(first_message.content) > 50 else (first_message.content if first_message else "New Chat")
        
        result.append({
            "id": session_id,
            "title": title,
            "last_activity": last_activity.isoformat() if last_activity else None,
            "created_at": created_at.isoformat() if created_at else None,
            "message_count": message_count,
        })
    
    return result


def delete_session(db: Session, session_id: str) -> bool:
    """Delete all messages for a session."""
    deleted = db.query(Message).filter(Message.session_id == session_id).delete()
    db.commit()
    return deleted > 0


def get_session_summary(db: Session, session_id: str) -> Optional[dict]:
    """Get summary information for a session."""
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    
    if not messages:
        return None
    
    first_message = next((m for m in messages if m.role == "user"), None)
    last_message = messages[-1] if messages else None
    
    return {
        "id": session_id,
        "message_count": len(messages),
        "created_at": messages[0].created_at.isoformat() if messages else None,
        "last_activity": last_message.created_at.isoformat() if last_message else None,
        "title": first_message.content[:50] + "..." if first_message and len(first_message.content) > 50 else (first_message.content if first_message else "New Chat"),
    }

