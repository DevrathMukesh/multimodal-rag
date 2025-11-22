from __future__ import annotations

import os
from typing import Any, Dict, List
import logging

from unstructured.partition.pdf import partition_pdf

from app.core.config import settings
from app.utils.file import save_json


def extract_elements(file_path: str) -> Dict[str, List[Any]]:
    """Extract text, tables, and images from a PDF using unstructured.

    Returns a dict with raw unstructured elements.
    When use_ollama_embeddings=False, images are skipped (text-only mode).
    """
    logging.info("Partitioning PDF: %s (Ollama embeddings: %s)", file_path, settings.use_ollama_embeddings)
    
    # Only extract images if Ollama embeddings are enabled
    extract_images = settings.use_ollama_embeddings
    
    chunks = partition_pdf(
        filename=file_path,
        infer_table_structure=True,
        strategy="hi_res",
        extract_image_block_types=["Image"] if extract_images else [],
        extract_image_block_to_payload=extract_images,
        chunking_strategy="by_title",
        max_characters=10000,
        combine_text_under_n_chars=2000,
        new_after_n_chars=6000,
    )

    tables: List[Any] = []
    texts: List[Any] = []

    for chunk in chunks:
        if "Table" in str(type(chunk)):
            tables.append(chunk)
        elif "CompositeElement" in str(type(chunk)):
            texts.append(chunk)

    # Extract images (base64 with page number/source if present)
    # Only if Ollama embeddings are enabled
    images: List[Dict[str, Any]] = []
    if extract_images:
        for chunk in chunks:
            if "CompositeElement" in str(type(chunk)):
                chunk_els = chunk.metadata.orig_elements
                for el in chunk_els:
                    if "Image" in str(type(el)):
                        images.append({
                            "b64": getattr(el.metadata, "image_base64", None),
                            "page_number": getattr(el.metadata, "page_number", getattr(chunk.metadata, "page_number", None)),
                            "source": getattr(chunk.metadata, "filename", os.path.basename(file_path)),
                        })
    else:
        logging.info("Image extraction skipped (Ollama embeddings disabled - text-only mode)")

    logging.info("Partitioned PDF into texts=%d tables=%d images=%d", len(texts), len(tables), len(images))
    return {"texts": texts, "tables": tables, "images": images}


def normalize_elements(raw: Dict[str, List[Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Normalize raw elements to serializable parents for storage and later use."""
    normalized_texts: List[Dict[str, Any]] = []
    for t in raw["texts"]:
        normalized_texts.append({
            "type": "text",
            "text": getattr(t, "text", ""),
            "page_number": getattr(t.metadata, "page_number", None),
            "source": getattr(t.metadata, "filename", None),
        })

    normalized_tables: List[Dict[str, Any]] = []
    for tbl in raw["tables"]:
        normalized_tables.append({
            "type": "table",
            "text": getattr(tbl, "text", None),
            "table_html": getattr(tbl.metadata, "text_as_html", None),
            "page_number": getattr(tbl.metadata, "page_number", None),
            "source": getattr(tbl.metadata, "filename", None),
        })

    normalized_images: List[Dict[str, Any]] = []
    for img in raw["images"]:
        normalized_images.append({
            "type": "image",
            "b64": img.get("b64"),
            "page_number": img.get("page_number"),
            "source": img.get("source"),
        })

    return {"texts": normalized_texts, "tables": normalized_tables, "images": normalized_images}


def persist_json(doc_dir: str, name: str, payload: Dict[str, Any]) -> str:
    """Persist JSON payload to file."""
    out_path = os.path.join(doc_dir, name)
    save_json(out_path, payload)
    logging.info("Persisted JSON to %s", out_path)
    return out_path


def process_pdf(file_path: str, doc_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    logging.info("Begin processing PDF %s", file_path)
    raw = extract_elements(file_path)
    normalized = normalize_elements(raw)
    persist_json(doc_dir, "parents.json", normalized)
    logging.info("Finished processing PDF -> parents.json written")
    return normalized


