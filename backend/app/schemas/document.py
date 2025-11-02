from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: str
    name: str
    pages: int
    createdAt: str


