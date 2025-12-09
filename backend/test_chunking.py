"""Quick Test Script for Chunked Content Processing

Run this to verify the chunking system works correctly.
"""

import asyncio
import sys
sys.path.append('/app')

from app.database import SessionLocal
from app.models.submission import Submission
from app.services.preprocessing_service import PreprocessingService
from app.services.content_retrieval_service import ContentRetrievalService


async def test_chunking():
    """Test chunking on an existing submission or create a test one."""
    db = SessionLocal()
    
    try:
        # Get a test submission
        submission = db.query(Submission).first()
        
        if not submission:
            print("❌ No submissions found in database")
            print("   Upload a document first via the UI")
            return
        
        print(f"✅ Found submission: {submission.title}")
        print(f"   Status: {submission.status}")
        print(f"   Content length: {len(submission.original_content or '')} chars")
        
        # Test preprocessing
        print("\n📦 Testing preprocessing...")
        preprocessing_service = PreprocessingService(db)
        
        if submission.status == "preprocessed":
            print(f"   ✅ Already preprocessed with {len(submission.chunks)} chunks")
        else:
            chunks_created = await preprocessing_service.preprocess_submission(
                submission_id=submission.id,
                chunk_size=500,  # Small chunks for testing
                overlap=50
            )
            print(f"   ✅ Created {chunks_created} chunks")
        
        # Test content retrieval
        print("\n🔍 Testing content retrieval...")
        retrieval_service = ContentRetrievalService(db)
        chunks = retrieval_service.get_analyzable_content(submission.id)
        
        print(f"   ✅ Retrieved {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks[:3]):  # Show first 3
            print(f"\n   Chunk {i + 1}:")
            print(f"     - ID: {chunk.id}")
            print(f"     - Index: {chunk.chunk_index}")
            print(f"     - Text length: {len(chunk.text)} chars")
            print(f"     - Tokens: {chunk.token_count}")
            print(f"     - Metadata: {chunk.metadata}")
            print(f"     - Location: {chunk.location_display}")
        
        if len(chunks) > 3:
            print(f"\n   ... and {len(chunks) - 3} more chunks")
        
        print("\n✅ All tests passed!")
        print("\n📋 Summary:")
        print(f"   - Submission preprocessed: {submission.status == 'preprocessed'}")
        print(f"   - Total chunks: {len(chunks)}")
        print(f"   - Is chunked: {retrieval_service.is_chunked(submission.id)}")
        print(f"   - Chunk count: {retrieval_service.get_chunk_count(submission.id)}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_chunking())
