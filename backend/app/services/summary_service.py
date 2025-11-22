from __future__ import annotations

import os
from typing import Any, Dict, List, cast
import logging
import random

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings
from app.services.llm_service import get_text_summarizer_llm, get_image_summarizer_llm
from app.utils.file import save_json
from app.utils.rate_limit import is_rate_limit_error, extract_wait_seconds_from_error
import time


def _summarize_one_internal(element_truncated: str, is_title_page: bool, max_retries: int = 3) -> str:
    """
    Internal function to call Gemini API for text/table summarization with rate limit retry.
    
    Handles rate limits with proper wait times extracted from Gemini's error messages,
    with jitter to prevent synchronized retries across parallel requests.
    """
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
    llm = get_text_summarizer_llm()
    chain = prompt | llm | StrOutputParser()
    
    last_error = None
    for attempt in range(max_retries):
        try:
            result = cast(str, chain.invoke({"element": element_truncated}))
            result = result.strip() if result else ""
            # Log successful summary generation
            if result:
                logging.debug("Text/table summary generated: len=%d chars", len(result))
            return result
        except Exception as e:
            last_error = e
            
            # Check if it's a rate limit error (checks wrapped exceptions too)
            if is_rate_limit_error(e):
                # Extract wait time from error message (checks wrapped exceptions)
                wait_time = extract_wait_seconds_from_error(e)
                
                if wait_time:
                    # Gemini provided a wait time - use it with jitter
                    jitter_percent = random.uniform(0.1, 0.2)
                    jitter = wait_time * jitter_percent
                    total_wait = wait_time + jitter
                    
                    logging.warning(
                        "⏸️  RATE LIMIT - Text/Table Summarization | "
                        "Gemini suggested: %.1fs | Jitter (%.0f%%): +%.1fs | "
                        "Total delay: %.1fs | Retry attempt %d/%d",
                        wait_time, jitter_percent * 100, jitter, total_wait, attempt + 1, max_retries
                    )
                    
                    time.sleep(total_wait)
                    
                    logging.info("✅ Wait complete (%.1fs). Retrying text/table summarization...", total_wait)
                    continue
                else:
                    # No wait time in error - use exponential backoff with jitter
                    base_wait = 60.0 * (2 ** attempt)
                    jitter_percent = random.uniform(0.1, 0.2)
                    jitter = base_wait * jitter_percent
                    total_wait = base_wait + jitter
                    
                    logging.warning(
                        "⏸️  RATE LIMIT - Text/Table (no wait time in error) | "
                        "Base backoff: %.1fs | Jitter (%.0f%%): +%.1fs | "
                        "Total delay: %.1fs | Retry attempt %d/%d",
                        base_wait, jitter_percent * 100, jitter, total_wait, attempt + 1, max_retries
                    )
                    
                    time.sleep(total_wait)
                    
                    logging.info("✅ Wait complete (%.1fs). Retrying text/table summarization...", total_wait)
                    continue
            else:
                # Not a rate limit error - re-raise immediately
                raise
    
    # All retries exhausted
    if last_error is None:
        raise RuntimeError("Retry loop completed without error - this should not happen")
    
    logging.error("❌ All retries exhausted for text/table summarization. Last error: %s", type(last_error).__name__)
    raise last_error


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

    try:
        result = _summarize_one_internal(element_truncated, is_title_page)
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
        
        logging.info("Text/table summary generated using Gemini %s (len=%d, page=%s)", 
                     settings.text_summarizer_model_id, len(result), page_number or "unknown")
        return result
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        error_lower = error_msg.lower()
        
        # Distinguish between permanent failures and temporary issues
        is_api_key_error = (
            "api key" in error_lower or 
            "api_key_invalid" in error_lower or 
            "invalid argument provided to gemini" in error_lower or
            "api key not valid" in error_lower or
            error_type == "ChatGoogleGenerativeAIError"
        )
        
        is_rate_limit = (
            "rate limit" in error_lower or
            "quota" in error_lower or
            "resource exhausted" in error_lower or
            "429" in error_msg or
            "too many requests" in error_lower
        )
        
        if is_api_key_error:
            # Permanent failure - API key is invalid
            logging.warning("Gemini API key invalid - skipping summary")
            return ""
        elif is_rate_limit:
            # Temporary failure - rate limited, but this should be handled by LangChain retries
            # If we reach here, retries were exhausted - log but don't fail the entire document
            logging.warning("Rate limit hit (retries exhausted) - using fallback text")
            # Use original text as fallback
            return element[:200] + "..." if len(element) > 200 else element
        else:
            # Other errors - log and use fallback
            short_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
            logging.warning("Summary generation failed: %s", short_error)
            return element[:200] + "..." if len(element) > 200 else element


def summarize_texts_and_tables(items: List[Any], progress_callback=None, start_progress: int = 10, end_progress: int = 80) -> List[str]:
    """
    Summarize texts and tables sequentially to avoid rate limit collisions.
    
    Processing in parallel causes multiple requests to hit rate limits simultaneously,
    and they all retry together, causing retry storms. Sequential processing prevents this.
    
    Args:
        items: List of text/table items to summarize
        progress_callback: Optional function(progress: int) to call after each chunk
        start_progress: Starting progress percentage (default 10)
        end_progress: Ending progress percentage (default 80)
    """
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
    
    logging.info("Summarizing %d text/table chunks sequentially to avoid rate limit collisions", len(inputs))
    if not inputs:
        return []
    
    results: List[str] = [""] * len(inputs)
    
    # Calculate progress increment per chunk
    total_chunks = len(inputs)
    progress_range = end_progress - start_progress
    progress_per_chunk = progress_range / total_chunks if total_chunks > 0 else 0
    
    # Process sequentially to avoid rate limit collisions
    for idx, (txt, page_num) in enumerate(inputs):
        try:
            # Add a small delay between requests to respect rate limits proactively
            # This helps prevent hitting the rate limit in the first place
            if idx > 0:
                delay = random.uniform(0.5, 1.5)  # 0.5-1.5 seconds between requests
                logging.debug("Adding delay %.1fs between text/table requests", delay)
                time.sleep(delay)
            
            summary = _summarize_one(txt, page_num)
            results[idx] = summary
            
            # Update progress after each chunk
            if progress_callback:
                current_progress = int(start_progress + (idx + 1) * progress_per_chunk)
                progress_callback(min(current_progress, end_progress))
            
            # Log progress with summary length
            if summary:
                logging.info("📝 Text/Table summarized: %d/%d completed | Summary len: %d chars", 
                           idx + 1, len(inputs), len(summary))
            else:
                logging.warning("⚠️  Text/Table summary empty: %d/%d completed", idx + 1, len(inputs))
        except Exception as e:
            # Short error log
            error_msg = str(e)[:80] + "..." if len(str(e)) > 80 else str(e)
            logging.warning("❌ Text/Table summarization failed: %d/%d completed | Error: %s", 
                          idx + 1, len(inputs), error_msg)
            results[idx] = ""
            # Still update progress even on error
            if progress_callback:
                current_progress = int(start_progress + (idx + 1) * progress_per_chunk)
                progress_callback(min(current_progress, end_progress))
    
    return results




def summarize_images(images_b64: List[str], progress_callback=None, start_progress: int = 10, end_progress: int = 80) -> List[str]:
    """
    Summarize images sequentially to avoid rate limit collisions.
    
    Processing images in parallel causes all requests to hit rate limits
    simultaneously, and they all retry together, causing retry storms.
    Sequential processing with delays between requests prevents this.
    
    Args:
        images_b64: List of base64-encoded images to summarize
        progress_callback: Optional function(progress: int) to call after each chunk
        start_progress: Starting progress percentage (default 10)
        end_progress: Ending progress percentage (default 80)
    """
    if not images_b64:
        return []

    def _summ_img_internal(b64: str, max_retries: int = 3) -> str:
        """
        Internal function to call Gemini API for image summarization with rate limit retry.
        
        Handles rate limits with proper wait times extracted from Gemini's error messages,
        with jitter to prevent synchronized retries across parallel requests.
        """
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
        
        last_error = None
        for attempt in range(max_retries):
            try:
                response = llm.invoke([message])
                result = response.content if hasattr(response, 'content') else str(response)
                result = result.strip() if result else ""
                # Log successful summary generation
                if result:
                    logging.debug("Image summary generated using Gemini %s: len=%d chars", 
                                settings.image_summarizer_model_id, len(result))
                return result
            except Exception as e:
                last_error = e
                
                # Check if it's a rate limit error (checks wrapped exceptions too)
                if is_rate_limit_error(e):
                    # Extract wait time from error message (checks wrapped exceptions)
                    wait_time = extract_wait_seconds_from_error(e)
                    
                    if wait_time:
                        # Gemini provided a wait time - use it with jitter and buffer
                        jitter_percent = random.uniform(0.1, 0.2)
                        jitter = wait_time * jitter_percent
                        buffer = wait_time * 0.1  # 10% extra buffer for safety
                        total_wait = wait_time + jitter + buffer
                        
                        logging.warning(
                            "⏸️  RATE LIMIT - Image Summarization | "
                            "Gemini suggested: %.1fs | Jitter (%.0f%%): +%.1fs | Buffer (10%%): +%.1fs | "
                            "Total delay: %.1fs | Retry attempt %d/%d",
                            wait_time, jitter_percent * 100, jitter, buffer, total_wait, attempt + 1, max_retries
                        )
                        
                        time.sleep(total_wait)
                        
                        logging.info("✅ Wait complete (%.1fs). Retrying image summarization...", total_wait)
                        continue
                    else:
                        # No wait time in error - use exponential backoff with jitter
                        base_wait = 60.0 * (2 ** attempt)
                        jitter_percent = random.uniform(0.1, 0.2)
                        jitter = base_wait * jitter_percent
                        total_wait = base_wait + jitter
                        
                        logging.warning(
                            "⏸️  RATE LIMIT - Image (no wait time in error) | "
                            "Base backoff: %.1fs | Jitter (%.0f%%): +%.1fs | "
                            "Total delay: %.1fs | Retry attempt %d/%d",
                            base_wait, jitter_percent * 100, jitter, total_wait, attempt + 1, max_retries
                        )
                        
                        time.sleep(total_wait)
                        
                        logging.info("✅ Wait complete (%.1fs). Retrying image summarization...", total_wait)
                        continue
                else:
                    # Not a rate limit error - re-raise immediately
                    raise
        
        # All retries exhausted
        if last_error is None:
            raise RuntimeError("Retry loop completed without error - this should not happen")
        
        logging.error("❌ All retries exhausted for image summarization. Last error: %s", type(last_error).__name__)
        raise last_error

    def _summ_img(b64: str) -> str:
        try:
            return _summ_img_internal(b64)
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            error_lower = error_msg.lower()
            
            is_api_key_error = (
                "api key" in error_lower or 
                "api_key_invalid" in error_lower or 
                "invalid argument provided to gemini" in error_lower or
                "api key not valid" in error_lower or
                error_type == "ChatGoogleGenerativeAIError"
            )
            
            is_rate_limit = (
                "rate limit" in error_lower or
                "quota" in error_lower or
                "resource exhausted" in error_lower or
                "429" in error_msg or
                "too many requests" in error_lower
            )
            
            if is_api_key_error:
                logging.warning("Gemini API key invalid - skipping image summary")
                return "[ERROR] API key invalid"
            elif is_rate_limit:
                logging.warning("Rate limit hit (retries exhausted) - skipping image summary")
                return "[ERROR] Rate limit exceeded"
            else:
                short_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                logging.warning("Image summarization failed: %s", short_error)
                return "[ERROR] image summarization failed"

    # Process images SEQUENTIALLY (max_workers=1) to avoid rate limit collisions
    # When multiple images are processed in parallel, they all hit rate limits together
    # and retry together, causing a retry storm. Sequential processing prevents this.
    results: List[str] = [""] * len(images_b64)
    logging.info("Processing %d images sequentially to avoid rate limit collisions", len(images_b64))
    
    # Calculate progress increment per chunk
    total_images = len(images_b64)
    progress_range = end_progress - start_progress
    progress_per_chunk = progress_range / total_images if total_images > 0 else 0
    
    for idx, b64 in enumerate(images_b64):
        try:
            # Add a small delay between requests to respect rate limits proactively
            # This helps prevent hitting the rate limit in the first place
            if idx > 0:
                delay = random.uniform(0.5, 1.5)  # 0.5-1.5 seconds between requests
                logging.debug("Adding delay %.1fs between image requests", delay)
                time.sleep(delay)
            
            summary = _summ_img(b64)
            results[idx] = summary
            
            # Update progress after each chunk
            if progress_callback:
                current_progress = int(start_progress + (idx + 1) * progress_per_chunk)
                progress_callback(min(current_progress, end_progress))
            
            # Log progress with summary length
            if summary and not summary.startswith("[ERROR"):
                summary_len = len(summary)
                logging.info("🖼️  Image summarized: %d/%d completed | Summary len: %d chars", 
                           idx + 1, len(images_b64), summary_len)
            else:
                logging.warning("⚠️  Image summary failed/empty: %d/%d completed", idx + 1, len(images_b64))
        except Exception as e:
            # Short error log
            error_msg = str(e)[:80] + "..." if len(str(e)) > 80 else str(e)
            logging.warning("❌ Image summarization failed: %d/%d completed | Error: %s", 
                          idx + 1, len(images_b64), error_msg)
            results[idx] = "[ERROR] image summarization failed"
            # Still update progress even on error
            if progress_callback:
                current_progress = int(start_progress + (idx + 1) * progress_per_chunk)
                progress_callback(min(current_progress, end_progress))
    
    return results


def build_summaries(parents: Dict[str, List[Dict[str, Any]]], progress_callback=None) -> Dict[str, List[str]]:
    """
    Build summaries for all content. Raises exception if failure rate is too high.
    
    Progress distribution (10-80%):
    - Images and text/tables share the 10-80% range proportionally
    - Each chunk (image or text/table) gets equal weight in progress
    - Progress updates after each chunk is completed
    - When Ollama embeddings are disabled, images are skipped
    
    Args:
        parents: Dictionary with 'images', 'texts', 'tables' keys
        progress_callback: Optional function(progress: int) to call with progress updates (0-100)
    """
    from app.core.config import settings
    
    # Progress range is 10-80% (70% total)
    PROGRESS_START = 10
    PROGRESS_END = 80
    
    # Skip images if Ollama embeddings are disabled
    if settings.use_ollama_embeddings:
        images = parents.get("images", [])
        images_b64 = [img.get("b64") for img in images if img.get("b64")]
    else:
        logging.info("Image summarization skipped (Ollama embeddings disabled - text-only mode)")
        images = []
        images_b64 = []
    
    text_and_tables = parents.get("texts", []) + parents.get("tables", [])
    
    total_chunks = len(images_b64) + len(text_and_tables)
    
    if total_chunks == 0:
        logging.info("No content to summarize")
        return {
            "text_table_summaries": [],
            "image_summaries": [],
        }
    
    # Calculate progress ranges - images come first, then text/tables
    # All chunks share the 10-80% range equally
    images_count = len(images_b64)
    text_count = len(text_and_tables)
    
    # Calculate where images end and text begins
    if images_count > 0:
        images_end_progress = PROGRESS_START + int((PROGRESS_END - PROGRESS_START) * images_count / total_chunks)
    else:
        images_end_progress = PROGRESS_START
    
    # Summarize images first (10% to images_end_progress) - only if Ollama is enabled
    if images_b64 and settings.use_ollama_embeddings:
        logging.info("Starting image summarization (%d images)...", len(images_b64))
        image_summaries = summarize_images(
            images_b64, 
            progress_callback=progress_callback,
            start_progress=PROGRESS_START,
            end_progress=images_end_progress
        )
        logging.info("Image summarization completed (progress: %d%%)", images_end_progress)
    else:
        image_summaries = []
        # If no images, start text/tables immediately
        if images_count == 0:
            images_end_progress = PROGRESS_START
    
    # Summarize text/tables (images_end_progress to 80%)
    if text_and_tables:
        logging.info("Starting text/table summarization (%d items)...", len(text_and_tables))
        text_table_summaries = summarize_texts_and_tables(
            text_and_tables,
            progress_callback=progress_callback,
            start_progress=images_end_progress,
            end_progress=PROGRESS_END
        )
        logging.info("Text/table summarization completed (progress: %d%%)", PROGRESS_END)
    else:
        text_table_summaries = []
    
    # Ensure we end at 80% after all summarization
    if progress_callback:
        progress_callback(PROGRESS_END)

    # Check if too many summaries failed (indicating a critical issue like invalid API key)
    # Count failures: empty strings, error messages, or very short summaries (< 20 chars)
    total_summaries = len(text_table_summaries) + len(image_summaries)
    if total_summaries == 0:
        # If there's nothing to summarize, that's okay
        logging.info("No content to summarize")
        return {
            "text_table_summaries": text_table_summaries,
            "image_summaries": image_summaries,
        }
    
    failed_count = 0
    valid_summaries_count = 0
    
    for summary in text_table_summaries:
        if not summary or len(summary.strip()) < 20 or summary.startswith("[ERROR]"):
            failed_count += 1
        else:
            valid_summaries_count += 1
    
    for summary in image_summaries:
        if not summary or summary.startswith("[ERROR]"):
            failed_count += 1
        else:
            valid_summaries_count += 1
    
    # If no valid summaries were generated at all, this is a critical failure
    if valid_summaries_count == 0 and total_summaries > 0:
        error_msg = f"Critical summarization failure: All {total_summaries} summaries failed. No valid summaries were generated. This likely indicates an API configuration issue (e.g., invalid API key)."
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    failure_rate = failed_count / total_summaries if total_summaries > 0 else 0
    
    # If more than 90% of summaries failed, this indicates a critical issue
    if failure_rate > 0.9:
        error_msg = f"Critical summarization failure: {failed_count}/{total_summaries} summaries failed ({failure_rate*100:.1f}% failure rate). This likely indicates an API configuration issue (e.g., invalid API key)."
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    if failed_count > 0:
        logging.warning(f"{failed_count}/{total_summaries} summaries failed, but failure rate ({failure_rate*100:.1f}%) is acceptable")

    return {
        "text_table_summaries": text_table_summaries,
        "image_summaries": image_summaries,
    }


def persist_summaries(doc_dir: str, summaries: Dict[str, List[str]]) -> str:
    """Persist summaries to JSON file."""
    out_path = os.path.join(doc_dir, "summaries.json")
    save_json(out_path, summaries)
    return out_path


