from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.message import Message


def get_messages_by_session(db: Session, session_id: str, limit: Optional[int] = None) -> List[Message]:
    """Get all messages for a session, ordered by creation time."""
    query = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc())
    if limit:
        query = query.limit(limit)
    return query.all()


def create_message(
    db: Session,
    *,
    session_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
    sources: Optional[List[Dict]] = None
) -> Message:
    """Create a new message in the database."""
    msg = Message(
        id=message_id or str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content,
        created_at=datetime.utcnow()
    )
    if sources is not None:
        msg.set_sources(sources)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

