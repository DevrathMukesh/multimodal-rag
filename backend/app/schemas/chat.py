from pydantic import BaseModel
from typing import Literal, Optional, List


class Source(BaseModel):
    parent_id: str
    type: Literal["text", "table", "image"]
    page_number: Optional[int] = None
    source: Optional[str] = None
    summary: str
    score: Optional[float] = None
    text: Optional[str] = None
    table_html: Optional[str] = None
    image_b64: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    sessionId: str
    documentId: Optional[str] = None
    includeImages: Optional[bool] = True
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


