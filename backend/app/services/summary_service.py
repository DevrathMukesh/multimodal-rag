from __future__ import annotations

import os
from typing import Any, Dict, List, cast
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings
from app.services.llm_service import get_text_summarizer_llm, get_image_summarizer_llm
from app.utils.file import save_json


def _summarize_one(element: str, page_number: int = None) -> str:
    """Summarize a single text element."""
    if not element or not element.strip():
        logging.warning("_summarize_one called with empty element")
        return ""
    
    # Truncate very long inputs to avoid context issues
    max_input_length = 2000
    element_truncated = element[:max_input_length] if len(element) > max_input_length else element
    
    # Detect if this might be a title/first page (contains paper title, authors, abstract)
    is_title_page = (
        page_number == 1 or 
        ("attention" in element.lower() and "all you need" in element.lower()) or
        ("abstract" in element.lower() and len(element) < 3000)
    )
    
    if is_title_page:
        prompt_text = (
            "Provide a concise summary of the following content. "
            "IMPORTANT: If this appears to be a title page or first page of a research paper, "
            "be sure to include the paper title and all author names in the summary. "
            "Also include the abstract or main topic. "
            "Preserve important metadata like author names, affiliations, and paper title.\n\n"
            "Content:\n{element}\n\n"
            "Summary:"
        )
    else:
        prompt_text = (
            "Provide a concise summary of the following content. "
            "Include only the main points and key information. "
            "Do not add explanations or meta-commentary.\n\n"
            "Content:\n{element}\n\n"
            "Summary:"
        )
    prompt = ChatPromptTemplate.from_template(prompt_text)

    try:
        llm = get_text_summarizer_llm()
        chain = prompt | llm | StrOutputParser()
        result = cast(str, chain.invoke({"element": element_truncated}))
        result = result.strip()
        
        # Remove common prefixes that models sometimes add
        prefixes_to_remove = [
            "Here's a concise summary:",
            "Summary:",
            "Here's a summary:",
            "The summary is:",
        ]
        for prefix in prefixes_to_remove:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
        
        # Fallback for empty or too short results
        if not result or len(result) < 10:
            logging.warning(f"Summary was empty or too short (len={len(result)}), using truncated original")
            result = element[:200] + "..." if len(element) > 200 else element
        
        logging.debug(f"Summary generated (len={len(result)})")
        return result
    except Exception as e:
        logging.error("Summary generation failed: %s", e, exc_info=True)
        # Return truncated original as fallback
        return element[:200] + "..." if len(element) > 200 else element


def summarize_texts_and_tables(items: List[Any]) -> List[str]:
    inputs: List[tuple[str, int]] = []
    for it in items:
        page_num = None
        text_content = ""
        if isinstance(it, dict):
            # normalized
            page_num = it.get("page_number")
            if it.get("type") == "table":
                text_content = it.get("table_html") or it.get("text") or ""
            else:
                text_content = it.get("text") or ""
        else:
            # raw unstructured fallback
            page_num = getattr(it.metadata, "page_number", None)
            if "Table" in str(type(it)):
                text_content = getattr(it.metadata, "text_as_html", "")
            else:
                text_content = getattr(it, "text", "")
        inputs.append((text_content, page_num))
    
    logging.info("Summarizing %d text/table chunks", len(inputs))
    if not inputs:
        return []
    results: List[str] = [""] * len(inputs)
    max_workers = max(1, int(settings.text_summarizer_max_workers))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(_summarize_one, txt, page_num): idx 
            for idx, (txt, page_num) in enumerate(inputs)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logging.warning("Summarization failed for item %d: %s", idx, e)
                results[idx] = ""
    return results




def summarize_images(images_b64: List[str]) -> List[str]:
    if not images_b64:
        return []

    def _summ_img(b64: str) -> str:
        try:
            prompt_text = (
                "Describe the image in detail. For context, the image is part of a research paper. "
                "Focus on key visual elements, text, diagrams, or any important information visible."
            )
            
            # Create message with image for vision model
            llm = get_image_summarizer_llm()
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    }
                ]
            )
            
            response = llm.invoke([message])
            result = response.content if hasattr(response, 'content') else str(response)
            logging.info("Image summary generated using Gemini %s (len=%d)", settings.image_summarizer_model_id, len(result))
            return result
        except Exception as e:
            logging.warning("Image summarization failed: %s", e)
            return f"[ERROR] image summarization failed: {e}"

    max_workers = max(1, int(settings.text_summarizer_max_workers))
    results: List[str] = [""] * len(images_b64)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(_summ_img, b64): idx for idx, b64 in enumerate(images_b64)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logging.warning("Image summarization failed (future): %s", e)
                results[idx] = f"[ERROR] image summarization failed: {e}"
    return results


def build_summaries(parents: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[str]]:
    # Summarize images first, then text/tables
    images = parents.get("images", [])
    images_b64 = [img.get("b64") for img in images if img.get("b64")]
    image_summaries = summarize_images(images_b64)
    
    text_and_tables = parents.get("texts", []) + parents.get("tables", [])
    text_table_summaries = summarize_texts_and_tables(text_and_tables)

    return {
        "text_table_summaries": text_table_summaries,
        "image_summaries": image_summaries,
    }


def persist_summaries(doc_dir: str, summaries: Dict[str, List[str]]) -> str:
    """Persist summaries to JSON file."""
    out_path = os.path.join(doc_dir, "summaries.json")
    save_json(out_path, summaries)
    return out_path


