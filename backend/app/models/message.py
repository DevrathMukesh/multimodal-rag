from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)  # 'user' | 'assistant'
    content = Column(Text)
    sources_json = Column(Text, nullable=True)  # JSON string of sources list
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_sources(self, sources: Optional[List[Dict[str, Any]]]) -> None:
        """Store sources as JSON string."""
        if sources:
            self.sources_json = json.dumps(sources, ensure_ascii=False)
        else:
            self.sources_json = None
    
    def get_sources(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve sources from JSON string."""
        if not self.sources_json:
            return None
        try:
            return json.loads(self.sources_json)
        except (json.JSONDecodeError, TypeError):
            return None


