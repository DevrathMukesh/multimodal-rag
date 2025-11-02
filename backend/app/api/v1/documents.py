from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timezone
from app.schemas.document import DocumentRead
from app.api.v1.deps import get_db
from app.repositories.document_repo import list_documents, delete_document
from app.core.config import settings
from app.services.vector_service import delete_vectors_for_document
import os
import shutil


router = APIRouter()


# Serve both with and without trailing slash to avoid 307 redirects
@router.get("", response_model=dict)
@router.get("/", response_model=dict)
def get_documents(db: Session = Depends(get_db)) -> dict:
    docs = list_documents(db)
    # Filter out failed documents - they shouldn't appear in the list
    items = [
        DocumentRead(
            id=d.id,
            name=d.name,
            pages=d.pages,
            status=getattr(d, "status", "completed"),  # Default to completed for old records
            progress=getattr(d, "progress", 0),
            createdAt=d.created_at.replace(tzinfo=timezone.utc).isoformat(),
        )
        for d in docs
        if getattr(d, "status", "completed") != "failed"  # Exclude failed documents
    ]
    return {"documents": [item.model_dump() for item in items]}


@router.delete("/{doc_id}", response_model=dict)
def remove_document(doc_id: str, db: Session = Depends(get_db)) -> dict:
    # 1) delete files: uploads dir and parents index
    uploads_dir = os.path.join(settings.uploads_dir, doc_id)
    if os.path.exists(uploads_dir):
        shutil.rmtree(uploads_dir, ignore_errors=True)

    parents_index_path = os.path.join(settings.data_dir, "parents_index", f"{doc_id}.json")
    if os.path.exists(parents_index_path):
        try:
            os.remove(parents_index_path)
        except OSError:
            pass

    # 2) delete vectors
    delete_vectors_for_document(doc_id)

    # 3) delete DB row
    ok = delete_document(db, id=doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}

