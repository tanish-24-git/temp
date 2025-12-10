import asyncio
import sys
from pathlib import Path

sys.path.append('/app')

from app.database import SessionLocal
from app.models.submission import Submission
from app.services.preprocessing_service import PreprocessingService
from app.services.content_retrieval_service import ContentRetrievalService

UPLOAD_DIR = Path("/app/uploads")

async def test_chunking():
    db = SessionLocal()
    try:
        # Use latest submission
        submission = db.query(Submission).order_by(Submission.submitted_at.desc()).first()

        if not submission:
            print("❌ No submissions found in database")
            return

        print(f"✅ Using submission: {submission.title}")
        print(f"   ID: {submission.id}")
        print(f"   Status: {submission.status}")
        print(f"   Content length: {len(submission.original_content or '')} chars")

        preprocessing_service = PreprocessingService(db)
        retrieval_service = ContentRetrievalService(db)

        # First, see if chunks already exist
        chunks = retrieval_service.get_analyzable_content(submission.id)

        if chunks:
            print(f"   ✅ Already has {len(chunks)} chunks, will not re-preprocess")
        else:
            print("   ⚙️  No chunks yet, running preprocessing...")
            await preprocessing_service.preprocess_submission(
                submission_id=submission.id,
                chunk_size=500,
                overlap=50,
            )
            chunks = retrieval_service.get_analyzable_content(submission.id)
            print(f"   ✅ Created {len(chunks)} chunks")

        # Prepare output directory
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        base = f"chunks_{submission.id}"

        # Write each chunk to its own file
        for chunk in chunks:
            fname = UPLOAD_DIR / f"{base}_{chunk.chunk_index}.txt"
            with fname.open("w", encoding="utf-8") as f:
                f.write(f"Chunk index: {chunk.chunk_index}\n")
                f.write(f"Token count: {chunk.token_count}\n")
                f.write(f"Metadata: {getattr(chunk, 'metadata', None)}\n")
                f.write("\n--- TEXT START ---\n\n")
                f.write(chunk.text or "")
            print(f"   📝 Wrote {fname}")

        # Write summary file
        summary_path = UPLOAD_DIR / f"{base}_summary.txt"
        with summary_path.open("w", encoding="utf-8") as f:
            f.write(f"Submission ID: {submission.id}\n")
            f.write(f"Title: {submission.title}\n")
            f.write(f"Status: {submission.status}\n")
            f.write(f"Original length: {len(submission.original_content or '')} chars\n")
            f.write(f"Total chunks: {len(chunks)}\n\n")
            for chunk in chunks:
                f.write(
                    f"Index={chunk.chunk_index}, "
                    f"len={len(chunk.text or '')}, "
                    f"tokens={chunk.token_count}\n"
                )
        print(f"   📄 Summary written to {summary_path}")

        print("\n✅ Dump complete. Open the files under backend/uploads on your host.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_chunking())
