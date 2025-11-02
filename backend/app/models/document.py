from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pages = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100 percentage
    created_at = Column(DateTime, default=datetime.utcnow)


