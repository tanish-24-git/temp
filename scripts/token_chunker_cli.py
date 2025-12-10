#!/usr/bin/env python3
"""
Token-Based Chunking CLI Tool

Command-line interface for testing token-based chunking locally.
Supports text files and PDFs with configurable chunk size and overlap.

Usage:
    python token_chunker_cli.py --file document.txt --chunk_tokens 900 --overlap 200 --out chunks.json
    python token_chunker_cli.py --file report.pdf --is_pdf --chunk_tokens 900 --overlap 200 --out pdf_chunks.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TokenChunker:
    """Standalone token-based chunker for CLI usage."""
    
    def __init__(self):
        self.tokenizer = None
        self.tokenizer_type = None
        self.nlp = None
        self.sentence_splitter_type = None
        self._init_tokenizer()
        self._init_sentence_splitter()
    
    def _init_tokenizer(self):
        """Initialize tokenizer with fallback hierarchy."""
        # Try tiktoken
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.tokenizer_type = "tiktoken"
            logger.info("✓ Using tiktoken tokenizer (cl100k_base)")
            return
        except Exception as e:
            logger.warning(f"✗ tiktoken unavailable: {e}")
        
        # Try transformers
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("gpt2", use_fast=True)
            self.tokenizer_type = "transformers"
            logger.info("✓ Using HuggingFace transformers tokenizer (gpt2)")
            return
        except Exception as e:
            logger.warning(f"✗ transformers unavailable: {e}")
        
        # Fallback to whitespace
        self.tokenizer = None
        self.tokenizer_type = "whitespace"
        logger.warning("⚠ Using whitespace tokenizer (fallback) - counts will be approximate")
    
    def _init_sentence_splitter(self):
        """Initialize sentence splitter with fallback."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.sentence_splitter_type = "spacy"
            logger.info("✓ Using spaCy sentence splitter")
        except Exception as e:
            logger.warning(f"✗ spaCy unavailable: {e}. Using regex fallback")
            self.nlp = None
            self.sentence_splitter_type = "regex"
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text.strip():
            return 0
        
        if self.tokenizer_type == "tiktoken":
            return len(self.tokenizer.encode(text))
        elif self.tokenizer_type == "transformers":
            return len(self.tokenizer.encode(text))
        else:
            return len(text.split())
    
    def _segment_sentences(self, text: str) -> List[str]:
        """Segment text into sentences."""
        if not text.strip():
            return []
        
        if self.sentence_splitter_type == "spacy" and self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            import re
            pattern = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(pattern, text)
            return [s.strip() for s in sentences if s.strip()]
    
    def chunk_text(
        self,
        text: str,
        chunk_tokens: int = 900,
        overlap_tokens: int = 200,
        page_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Token-based chunking with sentence awareness.
        
        Args:
            text: Input text
            chunk_tokens: Max tokens per chunk
            overlap_tokens: Token overlap between chunks
            page_number: Optional page number
            
        Returns:
            List of chunk dictionaries
        """
        if not text.strip():
            return []
        
        sentences = self._segment_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        current_sentences = []
        current_tokens = 0
        global_token_offset = 0
        char_offset = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            if current_tokens + sentence_tokens > chunk_tokens and current_sentences:
                # Finalize chunk
                chunk_text = " ".join(current_sentences)
                sentence_count = len(current_sentences)
                
                chunks.append({
                    "chunk_index": len(chunks),
                    "text": chunk_text,
                    "token_count": current_tokens,
                    "start_token": global_token_offset,
                    "end_token": global_token_offset + current_tokens,
                    "page_number": page_number,
                    "metadata": {
                        "char_offset_start": char_offset - len(chunk_text),
                        "char_offset_end": char_offset,
                        "chunk_method": "token_based",
                        "tokenizer_type": self.tokenizer_type,
                        "sentence_count": sentence_count
                    }
                })
                
                # Calculate overlap
                overlap_sentences = []
                overlap_count = 0
                for sent in reversed(current_sentences):
                    sent_tokens = self._count_tokens(sent)
                    if overlap_count + sent_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, sent)
                        overlap_count += sent_tokens
                    else:
                        break
                
                global_token_offset += (current_tokens - overlap_count)
                current_sentences = overlap_sentences
                current_tokens = overlap_count
            
            # Handle oversized sentences
            if sentence_tokens > chunk_tokens:
                if current_sentences:
                    chunk_text = " ".join(current_sentences)
                    chunks.append({
                        "chunk_index": len(chunks),
                        "text": chunk_text,
                        "token_count": current_tokens,
                        "start_token": global_token_offset,
                        "end_token": global_token_offset + current_tokens,
                        "page_number": page_number,
                        "metadata": {
                            "char_offset_start": char_offset - len(chunk_text),
                            "char_offset_end": char_offset,
                            "chunk_method": "token_based",
                            "tokenizer_type": self.tokenizer_type,
                            "sentence_count": len(current_sentences)
                        }
                    })
                    global_token_offset += current_tokens
                    current_sentences = []
                    current_tokens = 0
                
                # Split oversized sentence by words
                words = sentence.split()
                word_chunk = []
                word_tokens = 0
                
                for word in words:
                    wt = self._count_tokens(word)
                    if word_tokens + wt > chunk_tokens and word_chunk:
                        chunk_text = " ".join(word_chunk)
                        chunks.append({
                            "chunk_index": len(chunks),
                            "text": chunk_text,
                            "token_count": word_tokens,
                            "start_token": global_token_offset,
                            "end_token": global_token_offset + word_tokens,
                            "page_number": page_number,
                            "metadata": {
                                "char_offset_start": char_offset,
                                "char_offset_end": char_offset + len(chunk_text),
                                "chunk_method": "token_based",
                                "tokenizer_type": self.tokenizer_type,
                                "oversized_split": True
                            }
                        })
                        global_token_offset += word_tokens
                        char_offset += len(chunk_text) + 1
                        word_chunk = []
                        word_tokens = 0
                    
                    word_chunk.append(word)
                    word_tokens += wt
                
                if word_chunk:
                    chunk_text = " ".join(word_chunk)
                    chunks.append({
                        "chunk_index": len(chunks),
                        "text": chunk_text,
                        "token_count": word_tokens,
                        "start_token": global_token_offset,
                        "end_token": global_token_offset + word_tokens,
                        "page_number": page_number,
                        "metadata": {
                            "char_offset_start": char_offset,
                            "char_offset_end": char_offset + len(chunk_text),
                            "chunk_method": "token_based",
                            "tokenizer_type": self.tokenizer_type,
                            "oversized_split": True
                        }
                    })
                    global_token_offset += word_tokens
                
                char_offset += len(sentence) + 1
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens
                char_offset += len(sentence) + 1
        
        # Finalize last chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append({
                "chunk_index": len(chunks),
                "text": chunk_text,
                "token_count": current_tokens,
                "start_token": global_token_offset,
                "end_token": global_token_offset + current_tokens,
                "page_number": page_number,
                "metadata": {
                    "char_offset_start": char_offset - len(chunk_text),
                    "char_offset_end": char_offset,
                    "chunk_method": "token_based",
                    "tokenizer_type": self.tokenizer_type,
                    "sentence_count": len(current_sentences)
                }
            })
        
        return chunks
    
    def chunk_pdf(
        self,
        file_path: str,
        chunk_tokens: int = 900,
        overlap_tokens: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Chunk PDF with page-aware processing.
        
        Args:
            file_path: Path to PDF
            chunk_tokens: Max tokens per chunk
            overlap_tokens: Token overlap
            
        Returns:
            List of chunks with page numbers
        """
        try:
            import PyPDF2
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            sys.exit(1)
        
        # Extract pages
        pages = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                pages.append(page_text if page_text else "")
        
        logger.info(f"Extracted {len(pages)} pages from PDF")
        
        # Chunk each page
        all_chunks = []
        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            
            page_chunks = self.chunk_text(
                page_text,
                chunk_tokens,
                overlap_tokens,
                page_number=page_num
            )
            
            all_chunks.extend(page_chunks)
        
        # Update chunk indices globally
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_index"] = i
        
        return all_chunks


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Token-Based Chunking CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chunk text file
  python token_chunker_cli.py --file document.txt --chunk_tokens 900 --overlap 200 --out chunks.json
  
  # Chunk PDF file
  python token_chunker_cli.py --file report.pdf --is_pdf --out pdf_chunks.json
        """
    )
    
    parser.add_argument("--file", required=True, help="Input file path")
    parser.add_argument("--chunk_tokens", type=int, default=900, help="Max tokens per chunk (default: 900)")
    parser.add_argument("--overlap", type=int, default=200, help="Token overlap between chunks (default: 200)")
    parser.add_argument("--is_pdf", action="store_true", help="Process as PDF file")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Validate input file
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # Initialize chunker
    print("\n" + "=" * 60)
    print("Token-Based Chunking CLI")
    print("=" * 60)
    chunker = TokenChunker()
    print()
    
    # Process file
    logger.info(f"Processing: {args.file}")
    logger.info(f"Chunk Tokens: {args.chunk_tokens}")
    logger.info(f"Overlap Tokens: {args.overlap}")
    print()
    
    try:
        if args.is_pdf:
            chunks = chunker.chunk_pdf(
                str(file_path),
                chunk_tokens=args.chunk_tokens,
                overlap_tokens=args.overlap
            )
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            chunks = chunker.chunk_text(
                text,
                chunk_tokens=args.chunk_tokens,
                overlap_tokens=args.overlap
            )
        
        # Calculate statistics
        if chunks:
            token_counts = [c["token_count"] for c in chunks]
            avg_tokens = sum(token_counts) / len(token_counts)
            min_tokens = min(token_counts)
            max_tokens = max(token_counts)
            
            print("=" * 60)
            print("Results:")
            print("-" * 60)
            print(f"  Total Chunks: {len(chunks)}")
            print(f"  Average Token Count: {avg_tokens:.1f}")
            print(f"  Min Token Count: {min_tokens}")
            print(f"  Max Token Count: {max_tokens}")
            print("=" * 60)
            print()
        else:
            logger.warning("No chunks generated (empty file?)")
        
        # Write output
        output_path = Path(args.out)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Output written to: {args.out}")
        logger.info(f"✓ Successfully processed {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
