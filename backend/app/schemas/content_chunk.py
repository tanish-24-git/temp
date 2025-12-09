"""Pydantic schemas for ContentChunk API requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ChunkMetadata(BaseModel):
    """Metadata for content chunk traceability"""
    source_type: Optional[str] = None  # pdf, docx, html, markdown
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    chunk_method: Optional[str] = None  # sliding_window, semantic, sentence_boundary
    synthetic: bool = False  # True for backward compatibility chunks
    legacy_mode: bool = False  # True if generated from original_content
    
    class Config:
        extra = "allow"  # Allow additional metadata fields


class ContentChunkBase(BaseModel):
    """Base schema for content chunk"""
    text: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., ge=0, description="Order within document")
    token_count: int = Field(default=0, ge=0, description="Number of tokens")
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)


class ContentChunkCreate(ContentChunkBase):
    """Schema for creating a new chunk"""
    submission_id: UUID


class ContentChunkUpdate(BaseModel):
    """Schema for updating a chunk (rarely used)"""
    text: Optional[str] = None
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentChunkResponse(ContentChunkBase):
    """Schema for chunk API responses"""
    id: UUID
    submission_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChunkDTO(BaseModel):
    """
    Data Transfer Object for chunks used internally by services.
    
    This simplified version is used for passing chunks between services
    without full database model overhead.
    """
    id: UUID
    text: str
    chunk_index: int
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def location_display(self) -> str:
        """Generate human-readable location string"""
        parts = []
        
        if self.metadata.get("page_number"):
            parts.append(f"Page {self.metadata['page_number']}")
        
        if self.metadata.get("section_title"):
            parts.append(f"Section: {self.metadata['section_title']}")
        
        if self.metadata.get("char_offset_start") is not None:
            start = self.metadata['char_offset_start']
            end = self.metadata.get('char_offset_end', start + len(self.text))
            parts.append(f"Chars {start}-{end}")
        
        if not parts:
            parts.append(f"Chunk {self.chunk_index + 1}")
        
        return ", ".join(parts)
    
    class Config:
        from_attributes = True


class PreprocessingRequest(BaseModel):
    """Request schema for preprocessing a submission"""
    chunk_size: int = Field(
        default=1000,
        ge=500,
        le=5000,
        description="Characters per chunk"
    )
    overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Character overlap between chunks"
    )


class PreprocessingResponse(BaseModel):
    """Response schema for preprocessing operation"""
    success: bool
    submission_id: UUID
    chunks_created: int
    status: str
    message: Optional[str] = None


class ChunkListResponse(BaseModel):
    """Response schema for listing chunks"""
    submission_id: UUID
    submission_title: str
    submission_status: str
    total_chunks: int
    chunks: list[ContentChunkResponse]
