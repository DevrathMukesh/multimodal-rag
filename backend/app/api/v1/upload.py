from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.schemas.document import DocumentRead
from datetime import datetime, timezone
import uuid
import os
from typing import cast
from pypdf import PdfReader
from sqlalchemy.orm import Session
import logging

from app.api.v1.deps import get_db
from app.core.config import settings
from app.utils.file import ensure_dir
from app.repositories.document_repo import create_document
from app.services.pdf_service import process_pdf
from app.services.summary_service import build_summaries, persist_summaries
from app.services.vector_service import index_multivector


router = APIRouter()


@router.post("/upload", response_model=DocumentRead)
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentRead:
    # 0) validate content type and size (read into memory for now)
    logging.info("Upload received: filename=%s, content_type=%s", file.filename, file.content_type)
    if file.content_type not in settings.allowed_mime_types and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_mb}MB")

    # 1) generate id and storage paths
    doc_id = str(uuid.uuid4())
    doc_dir = os.path.join(settings.uploads_dir, doc_id)
    ensure_dir(doc_dir)
    file_path = os.path.join(doc_dir, file.filename)

    # 2) save file to disk
    with open(file_path, "wb") as f:
        f.write(data)
    logging.info("Saved file to %s (size=%d bytes)", file_path, len(data))

    # 3) compute pages
    try:
        reader = PdfReader(file_path)
        pages = len(cast(list, reader.pages))
    except Exception:
        pages = 0

    # 4) extract and summarize (sync for now)
    try:
        logging.info("Starting PDF processing for doc_id=%s", doc_id)
        parents = process_pdf(file_path, doc_dir)
        logging.info("PDF processed: texts=%d, tables=%d, images=%d", len(parents.get("texts", [])), len(parents.get("tables", [])), len(parents.get("images", [])))
        summaries = build_summaries(parents)
        logging.info("Summaries built: text_table=%d, images=%d", len(summaries.get("text_table_summaries", [])), len(summaries.get("image_summaries", [])))
        persist_summaries(doc_dir, summaries)
        logging.info("Persisted summaries to %s", os.path.join(doc_dir, "summaries.json"))
        index_multivector(doc_id, parents, summaries)
        logging.info("Indexed document into Chroma: doc_id=%s", doc_id)
    except Exception as e:
        logging.exception("Failed to process and index document")
        raise HTTPException(status_code=500, detail="Failed to process document") from e

    # 5) persist document row
    created_at = datetime.now(timezone.utc)
    doc = create_document(db, id=doc_id, name=file.filename, pages=pages, created_at=created_at)

    # 6) return response
    return DocumentRead(
        id=doc.id,
        name=doc.name,
        pages=doc.pages,
        createdAt=doc.created_at.replace(tzinfo=timezone.utc).isoformat(),
    )


