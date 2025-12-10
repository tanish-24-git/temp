"""Preprocessing Service

Handles document chunking with token-based metadata extraction.
Converts uploaded documents into analyzable chunks stored in database.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import re
import logging

from ..models.submission import Submission
from ..models.content_chunk import ContentChunk
from .content_parser import ContentParserService

logger = logging.getLogger(__name__)


class PreprocessingService:
    """
    Document chunking and preprocessing service with token-based chunking.
    
    Responsibilities:
    - Parse documents based on content type
    - Split content into token-aware chunks
    - Extract metadata (page numbers, token counts, offsets)
    - Store chunks in database with proper ordering
    
    Token-Based Chunking:
    - Uses tiktoken (primary), transformers (secondary), or whitespace (fallback)
    - Implements sentence-aware chunking with spaCy or regex fallback
    - Supports configurable chunk size and overlap in tokens
    - Generates comprehensive metadata for each chunk
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.content_parser = ContentParserService()
        
        # Initialize tokenizer with fallback hierarchy
        self.tokenizer = None
        self.tokenizer_type = None
        self._init_tokenizer()
        
        # Initialize sentence segmentation
        self.nlp = None
        self.sentence_splitter_type = None
        self._init_sentence_splitter()
    
    def _init_tokenizer(self):
        """Initialize tokenizer with fallback: tiktoken -> transformers -> whitespace."""
        # Try tiktoken (OpenAI tokenizer)
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.tokenizer_type = "tiktoken"
            logger.info("Using tiktoken tokenizer (cl100k_base)")
            return
        except Exception as e:
            logger.warning(f"tiktoken unavailable: {e}")
        
        # Try HuggingFace transformers
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("gpt2", use_fast=True)
            self.tokenizer_type = "transformers"
            logger.info("Using HuggingFace transformers tokenizer (gpt2)")
            return
        except Exception as e:
            logger.warning(f"transformers unavailable: {e}")
        
        # Fallback to whitespace tokenizer
        self.tokenizer = None
        self.tokenizer_type = "whitespace"
        logger.warning("Using whitespace tokenizer (fallback) - token counts will be approximate")
    
    def _init_sentence_splitter(self):
        """Initialize sentence splitter: spaCy -> regex fallback."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.sentence_splitter_type = "spacy"
            logger.info("Using spaCy sentence splitter (en_core_web_sm)")
        except Exception as e:
            logger.warning(f"spaCy unavailable: {e}. Using regex fallback.")
            self.nlp = None
            self.sentence_splitter_type = "regex"
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using available tokenizer."""
        if not text.strip():
            return 0
        
        if self.tokenizer_type == "tiktoken":
            return len(self.tokenizer.encode(text))
        elif self.tokenizer_type == "transformers":
            return len(self.tokenizer.encode(text))
        else:
            # Whitespace fallback
            return len(text.split())
    
    def _segment_sentences(self, text: str) -> List[str]:
        """Segment text into sentences using spaCy or regex."""
        if not text.strip():
            return []
        
        if self.sentence_splitter_type == "spacy" and self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Regex fallback: split on sentence-ending punctuation
            pattern = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(pattern, text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _split_oversized_sentence(
        self,
        sentence: str,
        chunk_tokens: int,
        overlap_tokens: int,
        start_token_offset: int,
        start_char_offset: int,
        page_number: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Split a sentence that exceeds token limit into multiple chunks.
        Uses word-level splitting to stay within token boundaries.
        """
        words = sentence.split()
        chunks = []
        current_words = []
        current_tokens = 0
        local_char_offset = start_char_offset
        
        for word in words:
            word_tokens = self._count_tokens(word)
            
            if current_tokens + word_tokens > chunk_tokens and current_words:
                # Finalize current chunk
                chunk_text = " ".join(current_words)
                chunks.append({
                    "text": chunk_text,
                    "token_count": current_tokens,
                    "metadata": {
                        "chunk_index": -1,  # Will be set by caller
                        "start_token": start_token_offset,
                        "end_token": start_token_offset + current_tokens,
                        "char_offset_start": local_char_offset,
                        "char_offset_end": local_char_offset + len(chunk_text),
                        "chunk_method": "token_based",
                        "page_number": page_number,
                        "oversized_split": True,
                        "tokenizer_type": self.tokenizer_type
                    }
                })
                
                start_token_offset += current_tokens
                local_char_offset += len(chunk_text) + 1
                current_words = []
                current_tokens = 0
            
            current_words.append(word)
            current_tokens += word_tokens
        
        # Add remaining words
        if current_words:
            chunk_text = " ".join(current_words)
            chunks.append({
                "text": chunk_text,
                "token_count": current_tokens,
                "metadata": {
                    "chunk_index": -1,
                    "start_token": start_token_offset,
                    "end_token": start_token_offset + current_tokens,
                    "char_offset_start": local_char_offset,
                    "char_offset_end": local_char_offset + len(chunk_text),
                    "chunk_method": "token_based",
                    "page_number": page_number,
                    "oversized_split": True,
                    "tokenizer_type": self.tokenizer_type
                }
            })
        
        return chunks
    
    def _token_based_chunker(
        self,
        text: str,
        chunk_tokens: int = 900,
        overlap_tokens: int = 200,
        page_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Token-based chunking with sentence awareness and overlap.
        
        Algorithm:
        1. Segment text into sentences
        2. Greedily pack sentences into chunks up to chunk_tokens limit
        3. Add overlap_tokens between consecutive chunks for context
        4. Handle oversized sentences by splitting at word boundaries
        
        Args:
            text: Input text to chunk
            chunk_tokens: Maximum tokens per chunk (default: 900)
            overlap_tokens: Token overlap between chunks (default: 200)
            page_number: PDF page number (optional)
            
        Returns:
            List of chunk dictionaries with text, token_count, and metadata
        """
        if not text.strip():
            return []
        
        # Step 1: Segment into sentences
        sentences = self._segment_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk_sentences = []
        current_token_count = 0
        global_token_offset = 0
        char_offset = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # Check if adding sentence exceeds limit
            if current_token_count + sentence_tokens > chunk_tokens and current_chunk_sentences:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk_sentences)
                sentence_count = len(current_chunk_sentences)
                
                chunks.append({
                    "text": chunk_text,
                    "token_count": current_token_count,
                    "metadata": {
                        "chunk_index": len(chunks),
                        "start_token": global_token_offset,
                        "end_token": global_token_offset + current_token_count,
                        "char_offset_start": char_offset - len(chunk_text),
                        "char_offset_end": char_offset,
                        "chunk_method": "token_based",
                        "page_number": page_number,
                        "tokenizer_type": self.tokenizer_type,
                        "sentence_count": sentence_count
                    }
                })
                
                # Calculate overlap for next chunk
                overlap_sentences = []
                overlap_count = 0
                for sent in reversed(current_chunk_sentences):
                    sent_tokens = self._count_tokens(sent)
                    if overlap_count + sent_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, sent)
                        overlap_count += sent_tokens
                    else:
                        break
                
                # Move global offset forward (accounting for overlap)
                global_token_offset += (current_token_count - overlap_count)
                
                # Reset for next chunk with overlap
                current_chunk_sentences = overlap_sentences
                current_token_count = overlap_count
            
            # Handle oversized sentences (> chunk_tokens)
            if sentence_tokens > chunk_tokens:
                # First, finalize any pending chunk
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    sentence_count = len(current_chunk_sentences)
                    
                    chunks.append({
                        "text": chunk_text,
                        "token_count": current_token_count,
                        "metadata": {
                            "chunk_index": len(chunks),
                            "start_token": global_token_offset,
                            "end_token": global_token_offset + current_token_count,
                            "char_offset_start": char_offset - len(chunk_text),
                            "char_offset_end": char_offset,
                            "chunk_method": "token_based",
                            "page_number": page_number,
                            "tokenizer_type": self.tokenizer_type,
                            "sentence_count": sentence_count
                        }
                    })
                    
                    global_token_offset += current_token_count
                    current_chunk_sentences = []
                    current_token_count = 0
                
                # Split oversized sentence
                split_chunks = self._split_oversized_sentence(
                    sentence,
                    chunk_tokens,
                    overlap_tokens,
                    global_token_offset,
                    char_offset,
                    page_number
                )
                
                # Update chunk indices
                for chunk in split_chunks:
                    chunk["metadata"]["chunk_index"] = len(chunks)
                    chunks.append(chunk)
                
                global_token_offset += sum(c["token_count"] for c in split_chunks)
                char_offset += len(sentence) + 1
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_token_count += sentence_tokens
                char_offset += len(sentence) + 1
        
        # Finalize last chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            sentence_count = len(current_chunk_sentences)
            
            chunks.append({
                "text": chunk_text,
                "token_count": current_token_count,
                "metadata": {
                    "chunk_index": len(chunks),
                    "start_token": global_token_offset,
                    "end_token": global_token_offset + current_token_count,
                    "char_offset_start": char_offset - len(chunk_text),
                    "char_offset_end": char_offset,
                    "chunk_method": "token_based",
                    "page_number": page_number,
                    "tokenizer_type": self.tokenizer_type,
                    "sentence_count": sentence_count
                }
            })
        
        return chunks
    
    async def preprocess_submission(
        self,
        submission_id: UUID,
        chunk_tokens: int = 900,  # Tokens per chunk
        overlap_tokens: int = 200  # Token overlap for context preservation
    ) -> int:
        """
        Preprocess a submission by chunking its content using token-based chunking.
        
        Args:
            submission_id: Submission to preprocess
            chunk_tokens: Target tokens per chunk (default: 900)
            overlap_tokens: Token overlap between consecutive chunks (default: 200)
            
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
                    chunk_tokens,
                    overlap_tokens
                )
            elif submission.content_type == "docx":
                chunks_data = await self._chunk_docx(
                    submission.file_path,
                    chunk_tokens,
                    overlap_tokens
                )
            elif submission.content_type in ["html", "markdown", "text"]:
                chunks_data = self._chunk_text(
                    submission.original_content or "",
                    chunk_tokens,
                    overlap_tokens,
                    submission.content_type
                )
            else:
                raise ValueError(f"Unsupported content type: {submission.content_type}")
            
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
            
            logger.info(f"Preprocessed submission {submission_id}: {len(chunks_data)} chunks created")
            return len(chunks_data)
            
        except Exception as e:
            submission.status = "failed"
            self.db.commit()
            logger.error(f"Preprocessing failed for {submission_id}: {str(e)}")
            raise Exception(f"Preprocessing failed: {str(e)}")
    
    async def _chunk_pdf(
        self,
        file_path: str,
        chunk_tokens: int,
        overlap_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Extract and chunk PDF with page number metadata.
        
        Uses page-aware chunking to preserve page boundaries for
        accurate violation location tracking.
        
        Args:
            file_path: Path to PDF file
            chunk_tokens: Target tokens per chunk
            overlap_tokens: Token overlap between chunks
            
        Returns:
            List of chunks with page_number metadata
        """
        # Extract pages separately
        pages = self.content_parser.extract_pdf_pages(file_path)
        
        all_chunks = []
        global_chunk_index = 0
        
        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            
            # Chunk each page separately with page number
            page_chunks = self._token_based_chunker(
                page_text,
                chunk_tokens,
                overlap_tokens,
                page_number=page_num
            )
            
            # Update global chunk indices
            for chunk in page_chunks:
                chunk["metadata"]["chunk_index"] = global_chunk_index
                global_chunk_index += 1
            
            all_chunks.extend(page_chunks)
        
        logger.info(f"Chunked PDF {file_path}: {len(pages)} pages -> {len(all_chunks)} chunks")
        return all_chunks
    
    async def _chunk_docx(
        self,
        file_path: str,
        chunk_tokens: int,
        overlap_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Extract and chunk DOCX with token-based chunking.
        
        Args:
            file_path: Path to DOCX file
            chunk_tokens: Target tokens per chunk
            overlap_tokens: Token overlap between chunks
            
        Returns:
            List of chunks
        """
        # Parse DOCX
        docx_content = self.content_parser.parse_docx(file_path)
        
        chunks = self._token_based_chunker(
            docx_content,
            chunk_tokens,
            overlap_tokens,
            page_number=None
        )
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        chunk_tokens: int,
        overlap_tokens: int,
        source_type: str
    ) -> List[Dict[str, Any]]:
        """
        Token-based text chunking (replaces character-based approach).
        
        Args:
            text: Text to chunk
            chunk_tokens: Target tokens per chunk
            overlap_tokens: Token overlap between chunks
            source_type: Document type for metadata
            
        Returns:
            List of chunk dictionaries with text, token_count, and metadata
        """
        return self._token_based_chunker(
            text,
            chunk_tokens,
            overlap_tokens,
            page_number=None
        )
    
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
