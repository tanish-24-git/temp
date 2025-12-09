"""KnowledgeBase SQLAlchemy Model"""

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..database import Base
import uuid


class KnowledgeBase(Base):
    """Stores regulatory documents for RAG."""
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    country_code = Column(String(10), nullable=False, index=True)
    regulation_name = Column(String(255), nullable=False, index=True)
    document_title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                        onupdate=func.now())
    
    def __repr__(self):
        return f"<KnowledgeBase {self.regulation_name} ({self.country_code})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "country_code": self.country_code,
            "regulation_name": self.regulation_name,
            "document_title": self.document_title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "metadata": self.metadata
        }
