"""ContentChunk SQLAlchemy Model

Stores individual chunks of preprocessed content with metadata for traceability.
Enables granular analysis and precise violation mapping.
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class ContentChunk(Base):
    """
    Individual chunk of preprocessed content.
    
    Chunks enable:
    - Processing documents larger than LLM context windows
    - Precise violation location tracking
    - Parallel chunk processing for performance
    - Source traceability via metadata
    
    Chunk Metadata Structure:
    {
        "source_type": "pdf" | "docx" | "html" | "markdown",
        "page_number": 3,  # For PDFs
        "section_title": "Risk Disclosures",  # For structured docs
        "char_offset_start": 1500,  # Character position in original
        "char_offset_end": 2500,
        "chunk_method": "sliding_window" | "semantic" | "sentence_boundary",
        "synthetic": false,  # True for backward compatibility chunks
        "legacy_mode": false  # True if generated from original_content
    }
    """
    __tablename__ = "content_chunks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    
    # Foreign key to submissions
    submission_id = Column(UUID(as_uuid=True), 
                          ForeignKey('submissions.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    
    # Ordering within document
    chunk_index = Column(Integer, nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    
    # Token count for context window management
    token_count = Column(Integer, default=0)
    
    # Metadata for traceability and display (renamed from 'metadata' to avoid SQLAlchemy conflict)
    chunk_metadata = Column(JSONB, default={}, server_default='{}')
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="chunks")
    
    def __repr__(self):
        return f"<ContentChunk submission_id={self.submission_id} index={self.chunk_index}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "submission_id": str(self.submission_id),
            "chunk_index": self.chunk_index,
            "text": self.text,
            "token_count": self.token_count,
            "metadata": self.chunk_metadata,  # Return as 'metadata' for API
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def get_location_display(self) -> str:
        """
        Generate human-readable location string from metadata.
        
        Examples:
        - "Page 3, Section: Risk Disclosures"
        - "Characters 1500-2500"
        - "Chunk 5"
        """
        parts = []
        
        if self.chunk_metadata.get("page_number"):
            parts.append(f"Page {self.chunk_metadata['page_number']}")
        
        if self.chunk_metadata.get("section_title"):
            parts.append(f"Section: {self.chunk_metadata['section_title']}")
        
        if self.chunk_metadata.get("char_offset_start") is not None:
            start = self.chunk_metadata['char_offset_start']
            end = self.chunk_metadata.get('char_offset_end', start + len(self.text))
            parts.append(f"Characters {start}-{end}")
        
        if not parts:
            parts.append(f"Chunk {self.chunk_index + 1}")
        
        return ", ".join(parts)
