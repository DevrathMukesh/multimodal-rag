from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.models.document import Document

def create_document(db: Session, *, id: str, name: str, pages: int, created_at: datetime | None = None) -> Document:
    doc = Document(id=id, name=name, pages=pages, created_at=created_at or datetime.utcnow())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(db: Session) -> List[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def delete_document(db: Session, *, id: str) -> bool:
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

