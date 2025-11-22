from __future__ import annotations

import os
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import chromadb
from langchain_chroma import Chroma

from app.core.config import settings
from app.utils.file import load_json, save_json

# Lazy imports for embedding providers (only import when needed)
if TYPE_CHECKING:
    from langchain_ollama import OllamaEmbeddings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings


def _parents_index_dir() -> str:
    path = os.path.join(settings.data_dir, "parents_index")
    os.makedirs(path, exist_ok=True)
    return path


def _parents_index_path(doc_id: str) -> str:
    return os.path.join(_parents_index_dir(), f"{doc_id}.json")


def _load_parents_index(doc_id: str) -> Dict[str, Any]:
    """Load parents index for a document."""
    path = _parents_index_path(doc_id)
    return load_json(path)


def _save_parents_index(doc_id: str, index: Dict[str, Any]) -> None:
    """Save parents index for a document."""
    path = _parents_index_path(doc_id)
    save_json(path, index)


def _get_embeddings() -> Any:
    """Get the appropriate embedding function based on configuration."""
    if settings.use_ollama_embeddings:
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-ollama is not installed. "
                "Install it with: pip install langchain-ollama "
                "or: poetry add langchain-ollama"
            )
        logging.info("Using Ollama embeddings: %s at %s", settings.embedding_model_id, settings.ollama_base_url)
        return OllamaEmbeddings(
            model=settings.embedding_model_id,
            base_url=settings.ollama_base_url,
        )
    else:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-google-genai is not installed. "
                "Install it with: pip install langchain-google-genai "
                "or: poetry add langchain-google-genai"
            )
        logging.info("Using Google Gemini embeddings API: %s", settings.embedding_api_model_id)
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required when using API embeddings. "
                "Set USE_OLLAMA_EMBEDDINGS=true to use local Ollama embeddings instead."
            )
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_api_model_id,
            google_api_key=settings.google_api_key,
        )


def _get_vectorstore() -> Chroma:
    """Get or create the ChromaDB vectorstore."""
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    embeddings = _get_embeddings()
    
    collection_name = "multi_modal_rag"
    
    try:
        return Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )
    except (KeyError, ValueError) as e:
        # Collection might be corrupted, try to delete and recreate
        logging.warning(f"ChromaDB collection error: {e}. Attempting to recreate...")
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass  # Collection might not exist
        
        # Recreate the collection
        return Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )


def index_multivector(doc_id: str, parents: Dict[str, List[Dict[str, Any]]], summaries: Dict[str, List[str]]) -> None:
    """Index summaries and link to original parents.

    parents: { texts: [...], tables: [...], images: [...] }
    summaries: { text_table_summaries: [...], image_summaries: [...] }
    """
    vectorstore = _get_vectorstore()

    text_and_tables: List[Dict[str, Any]] = parents.get("texts", []) + parents.get("tables", [])
    text_table_summaries: List[str] = summaries.get("text_table_summaries", [])

    images: List[Dict[str, Any]] = parents.get("images", [])
    image_summaries: List[str] = summaries.get("image_summaries", [])

    # build parent index for this doc
    parent_index = _load_parents_index(doc_id)

    # prepare child docs
    from langchain_core.documents import Document as LCDocument

    child_docs: List[LCDocument] = []

    # text + tables
    for i, parent in enumerate(text_and_tables):
        if i >= len(text_table_summaries):
            break
        parent_id = str(uuid.uuid4())
        parent_index[parent_id] = parent
        meta = {
            "doc_id": doc_id,
            "parent_id": parent_id,
            "type": parent.get("type"),
            "page_number": parent.get("page_number"),
            "source": parent.get("source"),
        }
        child_docs.append(LCDocument(page_content=text_table_summaries[i], metadata=meta))

    # images
    for i, parent in enumerate(images):
        if i >= len(image_summaries):
            break
        parent_id = str(uuid.uuid4())
        parent_index[parent_id] = parent
        meta = {
            "doc_id": doc_id,
            "parent_id": parent_id,
            "type": parent.get("type"),
            "page_number": parent.get("page_number"),
            "source": parent.get("source"),
        }
        child_docs.append(LCDocument(page_content=image_summaries[i], metadata=meta))

    # upsert into vectorstore and persist parent index
    if child_docs:
        vectorstore.add_documents(child_docs)
    _save_parents_index(doc_id, parent_index)


def retrieve_with_sources(
    query: str,
    *,
    k: int = 5,
    document_id: Optional[str] = None,
    include_images: bool = True,
) -> Dict[str, Any]:
    vectorstore = _get_vectorstore()

    where: Dict[str, Any] = {}
    if document_id:
        where["doc_id"] = document_id

    # langchain_community Chroma doesn't expose where in similarity_search directly
    # so we use the underlying collection through search kwargs, or filter later.
    # Easiest approach: retrieve more and filter by metadata doc_id.
    results: List[Tuple[Any, float]] = vectorstore.similarity_search_with_score(query, k=max(k * 3, 10))

    sources: List[Dict[str, Any]] = []
    parents_resolved: List[Any] = []
    
    # ChromaDB via LangChain returns distance scores (lower = better) for cosine distance
    # Normalize and convert to similarity scores (higher = better) for better interpretability
    raw_scores = [score for _, score in results if score is not None]
    normalization_factor = None
    is_distance = False
    max_score = 0.0
    
    if raw_scores:
        # Determine if scores are distances (typical range 0-2 for cosine) or similarities
        max_score = max(raw_scores)
        min_score = min(raw_scores)
        # If scores are in typical distance range (> 0.5 and < 2), they're likely distances
        is_distance = max_score > 0.5 and max_score < 2.5
        
        if is_distance:
            # Convert distance to similarity: similarity = 1 - (distance / max_distance)
            # Use max(2.0, max_score) as normalization factor for cosine distance
            normalization_factor = max(2.0, max_score * 1.1)  # Add 10% buffer

    # collect results by doc and resolve parents
    taken = 0
    for doc, raw_score in results:
        md = doc.metadata or {}
        if document_id and md.get("doc_id") != document_id:
            continue
        if not include_images and md.get("type") == "image":
            continue
        parent_id = md.get("parent_id")
        doc_id = md.get("doc_id")
        if not parent_id or not doc_id:
            continue
        pindex = _load_parents_index(doc_id)
        parent = pindex.get(parent_id)
        if not parent:
            continue

        # Normalize score to similarity (0-1 scale, higher = better)
        if normalization_factor and is_distance:
            # Convert distance to similarity: higher similarity = better match
            normalized_score = max(0.0, 1.0 - (raw_score / normalization_factor))
            # Ensure score is always positive and meaningful
            similarity_score = max(0.0, min(1.0, normalized_score))
        else:
            # If scores are already similarities, use as-is but normalize to 0-1
            if raw_score > 1.0:
                similarity_score = min(1.0, raw_score / max_score) if max_score > 0 else 0.0
            else:
                similarity_score = max(0.0, min(1.0, raw_score))

        src: Dict[str, Any] = {
            "parent_id": parent_id,
            "type": md.get("type"),
            "page_number": md.get("page_number"),
            "source": md.get("source"),
            "summary": doc.page_content,
            "score": round(similarity_score, 4),  # Normalized similarity score (higher = better)
            "raw_score": round(float(raw_score), 4),  # Keep original for debugging
        }
        if src["type"] == "image":
            src["image_b64"] = parent.get("b64")
        elif src["type"] == "table":
            src["table_html"] = parent.get("table_html")
            src["text"] = parent.get("text")
        else:
            src["text"] = parent.get("text")

        sources.append(src)
        parents_resolved.append(parent)
        taken += 1
        if taken >= k:
            break

    # Sort sources by normalized similarity score in descending order (higher score = better match)
    sources.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {"sources": sources, "parents": parents_resolved}



def delete_vectors_for_document(doc_id: str) -> None:
    """Delete all vectors for a given document id from Chroma."""
    vectorstore = _get_vectorstore()
    try:
        # langchain Chroma supports where filter
        vectorstore.delete(where={"doc_id": doc_id})
    except Exception:
        # Best-effort cleanup; ignore if collection missing
        pass

