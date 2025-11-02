from pydantic import BaseModel
from typing import Optional


class DocumentRead(BaseModel):
    id: str
    name: str
    pages: int
    status: Optional[str] = "completed"
    progress: Optional[int] = 0  # 0-100 percentage
    createdAt: str


