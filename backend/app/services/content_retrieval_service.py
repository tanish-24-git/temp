"""Content Retrieval Service

Unified abstraction layer for accessing submission content.
Provides consistent chunk-based interface regardless of whether
submission has been preprocessed or uses legacy monolithic content.

This service ensures backward compatibility while enabling chunk-aware analysis.
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
import uuid

from ..models.submission import Submission
from ..models.content_chunk import ContentChunk
from ..schemas.content_chunk import ChunkDTO


class ContentRetrievalService:
    """
    Unified content access layer.
    
    All analysis services (ComplianceEngine, DeepAnalysis, etc.) should use
    this service instead of directly accessing submission.original_content.
    
    Benefits:
    - Transparent chunk handling
    - Backward compatibility with legacy submissions  
    - Consistent API for all analysis services
    - Easy migration path for existing code
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_analyzable_content(
        self, 
        submission_id: UUID,
        include_metadata: bool = True
    ) -> List[ChunkDTO]:
        """
        Get content chunks for analysis.
        
        Returns:
        - If submission status == "preprocessed": Returns actual chunks from DB
        - Otherwise: Synthesizes single chunk from original_content (backward compat)
        
        Args:
            submission_id: Submission to retrieve content for
            include_metadata: Whether to include chunk metadata
            
        Returns:
            List of ChunkDTO objects ready for analysis
            
        Raises:
            ValueError: If submission not found
        """
        submission = self.db.query(Submission).filter_by(id=submission_id).first()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        # Check if submission has been preprocessed into chunks
        if submission.status == "preprocessed" and submission.chunks:
            return self._get_real_chunks(submission, include_metadata)
        else:
            return self._synthesize_legacy_chunk(submission)
    
    def _get_real_chunks(
        self, 
        submission: Submission,
        include_metadata: bool
    ) -> List[ChunkDTO]:
        """Convert database chunks to DTOs."""
        chunks = []
        
        for chunk in submission.chunks:
            chunks.append(ChunkDTO(
                id=chunk.id,
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                metadata=chunk.chunk_metadata if include_metadata else {}
            ))
        
        return chunks
    
    def _synthesize_legacy_chunk(self, submission: Submission) -> List[ChunkDTO]:
        """
        Create synthetic single chunk for backward compatibility.
        
        This allows existing non-chunked submissions to work seamlessly
        with chunk-aware analysis services.
        """
        # Truncate to 3000 chars (existing behavior)
        content = submission.original_content or ""
        truncated_content = content[:3000] if content else ""
        
        # Estimate token count (rough approximation)
        token_count = len(truncated_content.split())
        
        # Use DETERMINISTIC UUID based on submission ID
        # This ensures that subsequent calls (e.g., from frontend) get the same ID
        synthetic_id = uuid.uuid5(uuid.NAMESPACE_OID, str(submission.id))
        
        synthetic_chunk = ChunkDTO(
            id=synthetic_id,
            text=truncated_content,
            chunk_index=0,
            token_count=token_count,
            metadata={
                "synthetic": True,
                "legacy_mode": True,
                "source_type": submission.content_type,
                "truncated": len(content) > 3000,
                "original_length": len(content)
            }
        )
        
        return [synthetic_chunk]
    
    def get_chunk_by_id(self, chunk_id: UUID) -> ChunkDTO:
        """
        Retrieve a specific chunk by ID.
        
        Useful for violation detail views and debugging.
        """
        chunk = self.db.query(ContentChunk).filter_by(id=chunk_id).first()
        
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")
        
        return ChunkDTO(
            id=chunk.id,
            text=chunk.text,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            metadata=chunk.chunk_metadata
        )
    
    def is_chunked(self, submission_id: UUID) -> bool:
        """
        Check if submission has been chunked.
        
        Returns:
            True if submission is preprocessed with chunks, False otherwise
        """
        submission = self.db.query(Submission).filter_by(id=submission_id).first()
        
        if not submission:
            return False
        
        return submission.status == "preprocessed" and bool(submission.chunks)
    
    def get_chunk_count(self, submission_id: UUID) -> int:
        """Get total number of chunks for a submission."""
        count = self.db.query(ContentChunk).filter_by(
            submission_id=submission_id
        ).count()
        
        return count if count > 0 else 1  # At least 1 (synthetic) for legacy
