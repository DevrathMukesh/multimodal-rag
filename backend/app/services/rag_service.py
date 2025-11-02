from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.services.vector_service import retrieve_with_sources
from app.services.llm_service import get_chat_llm
from app.utils.rate_limit import with_rate_limit_retry


def build_prompt(
    question: str, 
    parents: list[dict], 
    conversation_history: Optional[List[Dict[str, str]]] = None,
    include_images: bool = True, 
    max_chars: int = 8000
) -> ChatPromptTemplate:
    context_text = ""
    for p in parents:
        if isinstance(p, dict) and p.get("type") in {"text", "table"}:
            txt = p.get("text") or ""
            if txt:
                context_text += txt

    context_text = context_text[:max_chars]
    
    # Build conversation context from history
    conversation_context = ""
    if conversation_history:
        conv_parts = []
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                conv_parts.append(f"User: {content}")
            elif role == "assistant":
                conv_parts.append(f"Assistant: {content}")
        if conv_parts:
            conversation_context = "\n\nPrevious conversation:\n" + "\n".join(conv_parts) + "\n"
    
    # Handle case when no documents are available
    if not context_text and not parents:
        prompt_text = f"""
You are a helpful AI assistant. Answer the following question using your general knowledge.
{conversation_context}
Note: No documents have been uploaded yet, so you cannot reference specific documents. Please answer based on your training data.

Current Question: {question}
"""
    else:
        prompt_text = f"""
Answer the question based only on the following context which can include text, tables, and the images below.
{conversation_context}
Context from documents:
{context_text}

Current Question: {question}
"""

    prompt_content: list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]

    if include_images:
        for p in parents:
            if isinstance(p, dict) and p.get("type") == "image" and p.get("b64"):
                prompt_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{p['b64']}"},
                    }
                )

    return ChatPromptTemplate.from_messages([HumanMessage(content=prompt_content)])


@with_rate_limit_retry(max_retries=3, default_wait=60.0)
def _chat_via_gemini(prompt: ChatPromptTemplate) -> str:
    """Generate answer using Gemini chat model."""
    parser = StrOutputParser()
    llm = get_chat_llm()
    chain = prompt | llm | parser
    return chain.invoke({})


def answer_question(
    question: str, 
    *, 
    document_id: str | None, 
    session_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    include_images: bool = True, 
    k: int = 5
) -> Dict[str, Any]:
    bundle = retrieve_with_sources(
        query=question,
        k=k,
        document_id=document_id,
        include_images=include_images,
    )

    parents = bundle.get("parents", [])

    # Use Gemini chat model for final answer; ignore images in chat prompt
    prompt = build_prompt(question, parents, conversation_history=conversation_history, include_images=False)
    answer = _chat_via_gemini(prompt)
    return {"answer": answer, "sources": bundle.get("sources", [])}


