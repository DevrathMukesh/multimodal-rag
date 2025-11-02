from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.document import Document

def create_document(db: Session, *, id: str, name: str, pages: int, status: str = "processing", created_at: datetime | None = None) -> Document:
    doc = Document(id=id, name=name, pages=pages, status=status, created_at=created_at or datetime.utcnow())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_status(db: Session, *, id: str, status: str, progress: int | None = None) -> bool:
    """Update document status and optionally progress."""
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        return False
    doc.status = status
    if progress is not None:
        doc.progress = progress
    db.commit()
    db.refresh(doc)
    return True


def get_document_by_id(db: Session, *, id: str) -> Optional[Document]:
    """Get a document by ID."""
    return db.query(Document).filter(Document.id == id).first()


def list_documents(db: Session) -> List[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def delete_document(db: Session, *, id: str) -> bool:
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

