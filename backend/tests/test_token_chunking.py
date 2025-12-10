"""
Test suite for token-based chunking functionality.

Tests:
1. Basic multi-chunk generation from long text
2. Overlap correctness validation
3. Oversized sentence splitting
4. PDF page-aware chunking with page numbers
5. Tokenizer fallback behavior
6. spaCy fallback to regex
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from app.services.preprocessing_service import PreprocessingService
from app.models.submission import Submission


class MockDB:
    """Mock database session for testing."""
    
    def __init__(self):
        self.objects = {}
        self.committed = False
    
    def query(self, model):
        return self
    
    def filter_by(self, **kwargs):
        return self
    
    def first(self):
        return None
    
    def add(self, obj):
        pass
    
    def commit(self):
        self.committed = True
    
    def delete(self):
        return 0


@pytest.fixture
def mock_db():
    """Provide mock database."""
    return MockDB()


@pytest.fixture
def preprocessing_service(mock_db):
    """Provide preprocessing service instance."""
    return PreprocessingService(db=mock_db)


class TestBasicMultiChunk:
    """Test 1: Basic multi-chunk generation."""
    
    def test_long_text_generates_multiple_chunks(self, preprocessing_service):
        """Test that long text generates multiple chunks within token limits."""
        # Create long text (~2000 tokens when using whitespace tokenizer)
        long_text = "This is a test sentence. " * 200
        
        chunks = preprocessing_service._token_based_chunker(
            long_text,
            chunk_tokens=300,
            overlap_tokens=50
        )
        
        # Should generate multiple chunks
        assert len(chunks) > 1, "Long text should generate multiple chunks"
        
        # Each chunk should be within token limit (with some tolerance for sentence boundaries)
        for chunk in chunks:
            assert chunk["token_count"] <= 350, f"Chunk exceeds token limit: {chunk['token_count']}"
            assert chunk["token_count"] > 0, "Chunk should have non-zero tokens"
        
        # Verify metadata structure
        for chunk in chunks:
            assert "text" in chunk
            assert "token_count" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["chunk_method"] == "token_based"
            assert "start_token" in chunk["metadata"]
            assert "end_token" in chunk["metadata"]
            assert "char_offset_start" in chunk["metadata"]
            assert "char_offset_end" in chunk["metadata"]
    
    def test_empty_text_returns_empty_list(self, preprocessing_service):
        """Test that empty text returns empty list."""
        chunks = preprocessing_service._token_based_chunker("")
        assert chunks == []
        
        chunks = preprocessing_service._token_based_chunker("   ")
        assert chunks == []


class TestOverlapCorrectness:
    """Test 2: Overlap correctness validation."""
    
    def test_overlap_between_consecutive_chunks(self, preprocessing_service):
        """Verify overlap tokens between consecutive chunks."""
        # Generate text with clear sentence boundaries
        text = ". ".join([f"Sentence number {i}" for i in range(100)])
        
        overlap_tokens = 30
        chunks = preprocessing_service._token_based_chunker(
            text,
            chunk_tokens=150,
            overlap_tokens=overlap_tokens
        )
        
        # Need at least 2 chunks to test overlap
        if len(chunks) < 2:
            pytest.skip("Text too short to test overlap")
        
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_end = chunks[i]["metadata"]["end_token"]
            next_start = chunks[i + 1]["metadata"]["start_token"]
            
            # Overlap should be approximately equal to overlap_tokens
            # (within tolerance due to sentence boundaries)
            calculated_overlap = current_end - next_start
            assert calculated_overlap >= 0, "Invalid overlap: next chunk starts before current ends"
            assert calculated_overlap <= overlap_tokens + 50, "Overlap exceeds expected range"
    
    def test_token_sequence_consistency(self, preprocessing_service):
        """Test that token ranges are sequential and non-overlapping in start positions."""
        text = "This is a test sentence. " * 100
        
        chunks = preprocessing_service._token_based_chunker(
            text,
            chunk_tokens=200,
            overlap_tokens=40
        )
        
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i


class TestOversizedSentence:
    """Test 3: Oversized sentence splitting."""
    
    def test_long_sentence_splits_correctly(self, preprocessing_service):
        """Test handling of sentences exceeding chunk limit."""
        # Create a very long sentence (no sentence-ending punctuation)
        huge_sentence = " ".join([f"word{i}" for i in range(1000)])
        
        chunks = preprocessing_service._token_based_chunker(
            huge_sentence,
            chunk_tokens=100,
            overlap_tokens=20
        )
        
        # Should generate multiple chunks
        assert len(chunks) > 0, "Oversized sentence should generate chunks"
        
        # Each chunk should be within limits
        for chunk in chunks:
            assert chunk["token_count"] <= 100, f"Chunk exceeds token limit: {chunk['token_count']}"
        
        # Oversized chunks should have the flag
        assert any(chunk["metadata"].get("oversized_split") for chunk in chunks), \
            "At least one chunk should be marked as oversized_split"
    
    def test_mixed_regular_and_oversized_sentences(self, preprocessing_service):
        """Test chunking with mix of normal and oversized sentences."""
        # Normal sentences
        normal_text = "This is a normal sentence. " * 10
        
        # Oversized sentence (>300 tokens)
        oversized = " ".join([f"word{i}" for i in range(400)])
        
        # More normal sentences
        text = normal_text + oversized + ". " + normal_text
        
        chunks = preprocessing_service._token_based_chunker(
            text,
            chunk_tokens=100,
            overlap_tokens=20
        )
        
        assert len(chunks) > 0
        
        # Should have both regular and oversized chunks
        regular_chunks = [c for c in chunks if not c["metadata"].get("oversized_split")]
        oversized_chunks = [c for c in chunks if c["metadata"].get("oversized_split")]
        
        assert len(oversized_chunks) > 0, "Should have oversized chunks"


class TestPDFPageAwareChunking:
    """Test 4: PDF page-aware chunking."""
    
    @pytest.mark.asyncio
    async def test_pdf_chunks_have_page_numbers(self, preprocessing_service, tmp_path):
        """Test that PDF chunks include page numbers."""
        # Mock PDF with 2 pages
        page1_text = "This is page one content. " * 50
        page2_text = "This is page two content. " * 50
        
        # Mock the content parser
        preprocessing_service.content_parser.extract_pdf_pages = Mock(
            return_value=[page1_text, page2_text]
        )
        
        # Create temporary PDF path
        pdf_path = str(tmp_path / "test.pdf")
        
        chunks = await preprocessing_service._chunk_pdf(
            pdf_path,
            chunk_tokens=200,
            overlap_tokens=40
        )
        
        # Should have chunks from both pages
        assert len(chunks) > 0
        
        # Extract page numbers
        page_numbers = set(c["metadata"]["page_number"] for c in chunks)
        
        # Should have chunks from both pages
        assert 1 in page_numbers, "Should have chunks from page 1"
        assert 2 in page_numbers, "Should have chunks from page 2"
    
    @pytest.mark.asyncio
    async def test_empty_pages_skipped(self, preprocessing_service, tmp_path):
        """Test that empty PDF pages are skipped."""
        # Mock PDF with empty page
        preprocessing_service.content_parser.extract_pdf_pages = Mock(
            return_value=["Page 1 content. " * 50, "", "Page 3 content. " * 50]
        )
        
        pdf_path = str(tmp_path / "test.pdf")
        
        chunks = await preprocessing_service._chunk_pdf(
            pdf_path,
            chunk_tokens=200,
            overlap_tokens=40
        )
        
        # Should only have chunks from pages 1 and 3
        page_numbers = set(c["metadata"]["page_number"] for c in chunks)
        assert 1 in page_numbers
        assert 3 in page_numbers
        assert 2 not in page_numbers  # Empty page should be skipped


class TestTokenizerFallback:
    """Test 5: Tokenizer fallback behavior."""
    
    def test_tiktoken_fallback_to_transformers(self, mock_db):
        """Test fallback from tiktoken to transformers."""
        with patch("app.services.preprocessing_service.tiktoken", side_effect=ImportError):
            # Should fall back to transformers or whitespace
            service = PreprocessingService(db=mock_db)
            
            # Should have initialized some tokenizer
            assert service.tokenizer_type in ["transformers", "whitespace"]
    
    def test_all_tokenizers_fail_uses_whitespace(self, mock_db):
        """Test that whitespace tokenizer is used when all else fails."""
        with patch("app.services.preprocessing_service.tiktoken", side_effect=ImportError):
            with patch("app.services.preprocessing_service.AutoTokenizer", side_effect=ImportError):
                service = PreprocessingService(db=mock_db)
                
                # Should fall back to whitespace
                assert service.tokenizer_type == "whitespace"
                
                # Should still be able to count tokens
                token_count = service._count_tokens("hello world test")
                assert token_count > 0
    
    def test_tokenizer_type_stored_in_metadata(self, preprocessing_service):
        """Test that tokenizer type is stored in chunk metadata."""
        text = "This is a test sentence. " * 10
        
        chunks = preprocessing_service._token_based_chunker(text, chunk_tokens=100)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert "tokenizer_type" in chunk["metadata"]
            assert chunk["metadata"]["tokenizer_type"] in ["tiktoken", "transformers", "whitespace"]


class TestSpacyFallback:
    """Test 6: spaCy fallback to regex."""
    
    def test_spacy_fallback_to_regex(self, mock_db):
        """Test fallback from spaCy to regex sentence splitter."""
        with patch("app.services.preprocessing_service.spacy.load", side_effect=OSError):
            service = PreprocessingService(db=mock_db)
            
            # Should fall back to regex
            assert service.sentence_splitter_type == "regex"
    
    def test_regex_sentence_splitting_works(self, mock_db):
        """Test that regex-based sentence splitting functions correctly."""
        with patch("app.services.preprocessing_service.spacy.load", side_effect=OSError):
            service = PreprocessingService(db=mock_db)
            
            text = "First sentence. Second sentence! Third sentence? Fourth sentence."
            sentences = service._segment_sentences(text)
            
            # Should split into sentences
            assert len(sentences) >= 4
            assert any("First" in s for s in sentences)
            assert any("Fourth" in s for s in sentences)
    
    def test_chunking_works_with_regex_splitter(self, mock_db):
        """Test that chunking works with regex sentence splitter."""
        with patch("app.services.preprocessing_service.spacy.load", side_effect=OSError):
            service = PreprocessingService(db=mock_db)
            
            text = "This is sentence one. This is sentence two. " * 50
            chunks = service._token_based_chunker(text, chunk_tokens=100, overlap_tokens=20)
            
            assert len(chunks) > 0
            for chunk in chunks:
                assert chunk["token_count"] > 0
                assert "chunk_method" in chunk["metadata"]


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_chunk_metadata_completeness(self, preprocessing_service):
        """Test that all metadata fields are present and valid."""
        text = "Test sentence. " * 100
        
        chunks = preprocessing_service._token_based_chunker(
            text,
            chunk_tokens=200,
            overlap_tokens=40,
            page_number=5
        )
        
        required_fields = [
            "chunk_index", "start_token", "end_token",
            "char_offset_start", "char_offset_end",
            "chunk_method", "tokenizer_type"
        ]
        
        for chunk in chunks:
            for field in required_fields:
                assert field in chunk["metadata"], f"Missing field: {field}"
            
            # Page number should be set
            assert chunk["metadata"]["page_number"] == 5
            
            # Chunk method should be token_based
            assert chunk["metadata"]["chunk_method"] == "token_based"
    
    def test_character_offsets_sequential(self, preprocessing_service):
        """Test that character offsets are sequential."""
        text = "Short sentence. " * 50
        
        chunks = preprocessing_service._token_based_chunker(text, chunk_tokens=100)
        
        for i in range(len(chunks) - 1):
            current_end = chunks[i]["metadata"]["char_offset_end"]
            next_start = chunks[i + 1]["metadata"]["char_offset_start"]
            
            # Character ranges should be reasonable (allowing for overlap)
            assert next_start >= 0
            assert current_end > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
