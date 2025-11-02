from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from app.schemas.document import DocumentRead
from datetime import datetime, timezone
import uuid
import os
from typing import cast
from pypdf import PdfReader
from sqlalchemy.orm import Session
import logging
import time

from app.api.v1.deps import get_db
from app.core.config import settings
from app.utils.file import ensure_dir
from app.repositories.document_repo import create_document, update_document_status
from app.services.pdf_service import process_pdf
from app.services.summary_service import build_summaries, persist_summaries
from app.services.vector_service import index_multivector


router = APIRouter()


def process_upload_background(doc_id: str, file_path: str, doc_dir: str, filename: str, pages: int):
    """Background task to process uploaded PDF."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    start_time = time.time()
    try:
        logging.info("Starting background processing for doc_id=%s", doc_id)
        update_document_status(db, id=doc_id, status="processing", progress=0)
        
        # 1) Extract PDF and chunk (0-10%)
        logging.info("[STEP 1/5] Starting PDF parsing and chunking...")
        pdf_start = time.time()
        
        parents = process_pdf(file_path, doc_dir)
        
        pdf_elapsed = time.time() - pdf_start
        num_texts = len(parents.get("texts", []))
        num_tables = len(parents.get("tables", []))
        num_images = len(parents.get("images", []))
        logging.info("[STEP 1/5] PDF parsing completed in %.1f seconds: texts=%d, tables=%d, images=%d", 
                    pdf_elapsed, num_texts, num_tables, num_images)
        # PDF parsing complete - 10%
        update_document_status(db, id=doc_id, status="processing", progress=10)

        # 2) Build summaries (10-80% - progress updates per chunk)
        logging.info("[STEP 2/5] Starting summarization (texts: %d, images: %d)...", num_texts + num_tables, num_images)
        summary_start = time.time()
        
        # Progress callback to update during summarization (10-80% range)
        def update_summary_progress(progress: int):
            update_document_status(db, id=doc_id, status="processing", progress=progress)
        
        try:
            summaries = build_summaries(parents, progress_callback=update_summary_progress)
        except Exception as e:
            # Short error message
            error_str = str(e).lower()
            if "api key" in error_str or "api_key" in error_str:
                # Permanent failure - API key is invalid
                error_msg = "API key invalid - check GOOGLE_API_KEY in .env"
                logging.error(error_msg)
                update_document_status(db, id=doc_id, status="failed", progress=0)
                return
            elif "rate limit" in error_str or "quota" in error_str or "resource exhausted" in error_str:
                # Temporary failure - rate limit hit after retries exhausted
                # Note: LangChain should have retried, but if we're here, retries failed
                error_msg = "Rate limit/quota exceeded after retries - check Google API quotas or try later"
                logging.error(error_msg)
                update_document_status(db, id=doc_id, status="failed", progress=0)
                return
            else:
                # Other errors
                short_error = str(e)[:150] + "..." if len(str(e)) > 150 else str(e)
                error_msg = f"Summary generation failed: {short_error}"
                logging.error(error_msg)
                update_document_status(db, id=doc_id, status="failed", progress=0)
                return
        
        summary_elapsed = time.time() - summary_start
        logging.info("[STEP 2/5] Summarization completed in %.1f seconds: text_table=%d, images=%d", 
                    summary_elapsed,
                    len(summaries.get("text_table_summaries", [])), 
                    len(summaries.get("image_summaries", [])))
        # Summarization complete - should be at 80% (set by build_summaries)
        update_document_status(db, id=doc_id, status="processing", progress=80)
        
        # 3) Save summaries (80-90%)
        logging.info("[STEP 3/5] Saving summaries to JSON...")
        persist_summaries(doc_dir, summaries)
        logging.info("[STEP 3/5] Persisted summaries to %s", os.path.join(doc_dir, "summaries.json"))
        update_document_status(db, id=doc_id, status="processing", progress=90)
        
        # 4) Index document (90-100%)
        logging.info("[STEP 4/5] Indexing document into vector database...")
        index_start = time.time()
        
        try:
            index_multivector(doc_id, parents, summaries)
            index_elapsed = time.time() - index_start
            logging.info("[STEP 4/5] Indexing completed in %.1f seconds: doc_id=%s", index_elapsed, doc_id)
        except Exception as e:
            # Short error message
            error_str = str(e).lower()
            if "ollama" in error_str or "connection" in error_str:
                error_msg = f"Ollama connection failed - check if Ollama is running at {settings.ollama_base_url}"
                logging.error(error_msg)
            elif "chroma" in error_str or "chromadb" in error_str:
                error_msg = "ChromaDB error - check configuration"
                logging.error(error_msg)
            else:
                short_error = str(e)[:150] + "..." if len(str(e)) > 150 else str(e)
                error_msg = f"Indexing failed: {short_error}"
                logging.error(error_msg)
            update_document_status(db, id=doc_id, status="failed", progress=0)
            return

        # 5) Mark as completed (100%)
        total_elapsed = time.time() - start_time
        logging.info("[STEP 5/5] Finalizing document...")
        update_document_status(db, id=doc_id, status="completed", progress=100)
        
        logging.info("✓ Document processing completed in %.1f seconds: id=%s", total_elapsed, doc_id)
        logging.info("  Breakdown: PDF parsing=%.1fs, Summarization=%.1fs, Indexing=%.1fs", 
                    pdf_elapsed, summary_elapsed, index_elapsed)
    except Exception as e:
        # Short error message
        error_str = str(e).lower()
        if "api key" in error_str:
            error_msg = "CRITICAL: API key invalid - set GOOGLE_API_KEY in .env"
            logging.error(error_msg)
        elif "ollama" in error_str:
            error_msg = "CRITICAL: Ollama not accessible - start Ollama service"
            logging.error(error_msg)
        else:
            short_error = str(e)[:150] + "..." if len(str(e)) > 150 else str(e)
            error_msg = f"Background processing failed: {short_error}"
            logging.error(error_msg)
        try:
            update_document_status(db, id=doc_id, status="failed", progress=0)
        except Exception as db_error:
            logging.error("Failed to update document status: %s", str(db_error)[:100])
    finally:
        db.close()


@router.post("/upload", response_model=DocumentRead)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
) -> DocumentRead:
    logging.info("Upload received: filename=%s, content_type=%s", file.filename, file.content_type)
    
    # Validate content type
    if file.content_type not in settings.allowed_mime_types and not (file.filename and file.filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file data
    try:
        file_data = await file.read()
    except Exception as e:
        logging.error(f"Failed to read upload file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Validate file size
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(file_data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.max_upload_mb}MB")
    
    filename = file.filename or "document.pdf"
    
    try:
        # 1) Generate id and storage paths
        doc_id = str(uuid.uuid4())
        doc_dir = os.path.join(settings.uploads_dir, doc_id)
        ensure_dir(doc_dir)
        file_path = os.path.join(doc_dir, filename)

        # 2) Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_data)
        logging.info("Saved file to %s (size=%d bytes)", file_path, len(file_data))

        # 3) Compute pages (quick operation, done synchronously)
        try:
            reader = PdfReader(file_path)
            pages = len(cast(list, reader.pages))
        except Exception:
            pages = 0

        # 4) Create document immediately with "processing" status
        created_at = datetime.now(timezone.utc)
        doc = create_document(db, id=doc_id, name=filename, pages=pages, status="processing", created_at=created_at)
        logging.info("Document created in database: id=%s, name=%s, status=processing", doc.id, doc.name)

        # 5) Start background processing
        background_tasks.add_task(process_upload_background, doc_id, file_path, doc_dir, filename, pages)
        logging.info("Background processing task added for doc_id=%s", doc_id)
                
        # Return immediately with processing status
        return DocumentRead(
            id=doc.id,
            name=doc.name,
            pages=doc.pages,
            status=doc.status,
            progress=getattr(doc, "progress", 0),
            createdAt=doc.created_at.replace(tzinfo=timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/status/{doc_id}", response_model=DocumentRead)
async def get_upload_status(doc_id: str, db: Session = Depends(get_db)) -> DocumentRead:
    """Get upload status by document ID."""
    from app.repositories.document_repo import get_document_by_id
    
    doc = get_document_by_id(db, id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentRead(
        id=doc.id,
        name=doc.name,
        pages=doc.pages,
        status=doc.status,
        progress=getattr(doc, "progress", 0),
        createdAt=doc.created_at.replace(tzinfo=timezone.utc).isoformat(),
    )


