"""Preprocessing Service

Handles document chunking with metadata extraction.
Converts uploaded documents into analyzable chunks stored in database.
"""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import re

from ..models.submission import Submission
from ..models.content_chunk import ContentChunk
from .content_parser import ContentParserService


class PreprocessingService:
    """
    Document chunking and preprocessing service.
    
    Responsibilities:
    - Parse documents based on content type
    - Split content into manageable chunks
    - Extract metadata (page numbers, sections, etc.)
    - Store chunks in database with proper ordering
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.content_parser = ContentParserService()
    
    async def preprocess_submission(
        self,
        submission_id: UUID,
        chunk_size: int = 1000,  # Characters per chunk
        overlap: int = 100  # Character overlap for context preservation
    ) -> int:
        """
        Preprocess a submission by chunking its content.
        
        Args:
            submission_id: Submission to preprocess
            chunk_size: Target characters per chunk (500-5000)
            overlap: Character overlap between consecutive chunks
            
        Returns:
            Number of chunks created
            
        Raises:
            ValueError: If submission not found or already preprocessed
            Exception: If preprocessing fails
        """
        submission = self.db.query(Submission).filter_by(id=submission_id).first()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        # Skip if already preprocessed
        if submission.status == "preprocessed":
            return len(submission.chunks)
        
        # Update status to preprocessing
        submission.status = "preprocessing"
        self.db.commit()
        
        try:
            # Parse and chunk based on content type
            if submission.content_type == "pdf":
                chunks_data = await self._chunk_pdf(
                    submission.file_path, 
                    chunk_size, 
                    overlap
                )
            elif submission.content_type == "docx":
                chunks_data = await self._chunk_docx(
                    submission.file_path, 
                    chunk_size, 
                    overlap
                )
            elif submission.content_type in ["html", "markdown"]:
                chunks_data = self._chunk_text(
                    submission.original_content or "",
                    chunk_size,
                    overlap,
                    submission.content_type
                )
            else:
                # Fallback to simple text chunking
                chunks_data = self._chunk_text(
                    submission.original_content or "",
                    chunk_size,
                    overlap,
                    "text"
                )
            
            # Store chunks in database
            for idx, chunk_data in enumerate(chunks_data):
                chunk = ContentChunk(
                    submission_id=submission_id,
                    chunk_index=idx,
                    text=chunk_data["text"],
                    token_count=chunk_data["token_count"],
                    metadata=chunk_data["metadata"]
                )
                self.db.add(chunk)
            
            # Update submission status
            submission.status = "preprocessed"
            self.db.commit()
            
            return len(chunks_data)
            
        except Exception as e:
            submission.status = "failed"
            self.db.commit()
            raise Exception(f"Preprocessing failed: {str(e)}")
    
    async def _chunk_pdf(
        self, 
        file_path: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, Any]]:
        """
        Extract and chunk PDF with page number metadata.
        
        Uses ContentParserService to extract PDF content, then chunks
        with page number tracking for precise violation location.
        """
        # Parse PDF to get page-level content
        pdf_content = self.content_parser.parse_pdf(file_path)
        
        # For now, concatenate all pages and chunk
        # TODO: Implement page-aware chunking
        full_text = pdf_content
        
        chunks = self._chunk_text(
            full_text,
            chunk_size,
            overlap,
            "pdf"
        )
        
        # TODO: Add page number detection logic
        # For each chunk, determine which page(s) it spans
        
        return chunks
    
    async def _chunk_docx(
        self, 
        file_path: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, Any]]:
        """
        Extract and chunk DOCX with section metadata.
        
        Uses ContentParserService to extract DOCX content, then chunks
        with section heading tracking.
        """
        # Parse DOCX
        docx_content = self.content_parser.parse_docx(file_path)
        
        chunks = self._chunk_text(
            docx_content,
            chunk_size,
            overlap,
            "docx"
        )
        
        # TODO: Add section heading detection
        
        return chunks
    
    def _chunk_text(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int,
        source_type: str
    ) -> List[Dict[str, Any]]:
        """
        Simple text chunking with sliding window.
        
        Uses character-based chunking with overlap to preserve context
        across chunk boundaries. Respects sentence boundaries where possible.
        
        Args:
            text: Text to chunk
            chunk_size: Target characters per chunk
            overlap: Character overlap between chunks
            source_type: Document type for metadata
            
        Returns:
            List of chunk dictionaries with text, token_count, and metadata
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate chunk end position
            end = min(start + chunk_size, text_length)
            
            # Try to break on sentence boundary if not at document end
            if end < text_length and end - start > chunk_size // 2:
                # Look for sentence-ending punctuation near the end
                search_start = max(start, end - 100)
                sentence_end = self._find_sentence_boundary(text, search_start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk_text = text[start:end]
            
            # Skip empty chunks
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "token_count": len(chunk_text.split()),
                    "metadata": {
                        "source_type": source_type,
                        "char_offset_start": start,
                        "char_offset_end": end,
                        "chunk_method": "sliding_window_sentence_aware"
                    }
                })
            
            # Move to next chunk with overlap
            start = end - overlap if end < text_length else text_length
            
            # Prevent infinite loop
            if start >= end:
                start = end
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find the last sentence-ending punctuation within range.
        
        Returns position after the punctuation, or end if not found.
        """
        # Look for sentence endings: . ! ? followed by space or newline
        pattern = r'[.!?][\s\n]'
        matches = list(re.finditer(pattern, text[start:end]))
        
        if matches:
            # Return position after the last sentence ending
            last_match = matches[-1]
            return start + last_match.end()
        
        return end
    
    def delete_chunks(self, submission_id: UUID) -> int:
        """
        Delete all chunks for a submission.
        
        Useful for re-preprocessing with different parameters.
        
        Returns:
            Number of chunks deleted
        """
        count = self.db.query(ContentChunk).filter_by(
            submission_id=submission_id
        ).delete()
        
        # Reset submission status
        submission = self.db.query(Submission).filter_by(id=submission_id).first()
        if submission:
            submission.status = "uploaded"
        
        self.db.commit()
        return count
