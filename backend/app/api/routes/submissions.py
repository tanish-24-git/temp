from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from ...database import get_db
from ...models.submission import Submission
from ...services.content_parser import content_parser
from ...services.compliance_engine import compliance_engine
from ...schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionAnalyzeResponse
)
from ...config import settings

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("/upload", response_model=SubmissionResponse)
async def upload_submission(
    title: str = Form(...),
    content_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new submission."""
    try:
        # Validate content type
        if content_type not in ["html", "markdown", "pdf", "docx"]:
            raise HTTPException(400, "Invalid content type")

        # Create uploads directory if not exists
        os.makedirs(settings.upload_dir, exist_ok=True)

        # Save file
        file_id = uuid.uuid4()
        file_extension = {
            "html": ".html",
            "markdown": ".md",
            "pdf": ".pdf",
            "docx": ".docx"
        }[content_type]

        file_path = os.path.join(settings.upload_dir, f"{file_id}{file_extension}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Parse content
        parsed_content = await content_parser.parse_content(file_path, content_type)

        # Create submission
        submission = Submission(
            title=title,
            content_type=content_type,
            original_content=parsed_content,
            file_path=file_path,
            status="pending"
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        return submission

    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@router.get("", response_model=List[SubmissionResponse])
def list_submissions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all submissions."""
    submissions = db.query(Submission).order_by(
        Submission.submitted_at.desc()
    ).offset(skip).limit(limit).all()

    return submissions


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get submission details."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(404, "Submission not found")

    return submission


@router.post("/{submission_id}/analyze", response_model=SubmissionAnalyzeResponse)
async def analyze_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Trigger compliance analysis for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(404, "Submission not found")

    if submission.status == "analyzing":
        raise HTTPException(400, "Analysis already in progress")

    # Trigger analysis (async in background in production)
    try:
        await compliance_engine.analyze_submission(str(submission_id), db)

        return {
            "message": "Analysis completed",
            "submission_id": submission_id
        }

    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.delete("/{submission_id}")
def delete_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a submission and its associated file."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(404, "Submission not found")

    # Delete physical file if exists
    if submission.file_path and os.path.exists(submission.file_path):
        os.remove(submission.file_path)

    db.delete(submission)
    db.commit()

    return {"message": "Submission deleted successfully"}


@router.delete("")
def delete_all_submissions(
    db: Session = Depends(get_db)
):
    """Delete all submissions and their associated files."""
    submissions = db.query(Submission).all()

    deleted_count = 0
    failed_files = []

    for submission in submissions:
        # Delete physical file if exists
        if submission.file_path and os.path.exists(submission.file_path):
            try:
                os.remove(submission.file_path)
            except Exception as e:
                failed_files.append(submission.file_path)

        db.delete(submission)
        deleted_count += 1

    db.commit()

    message = f"Successfully deleted {deleted_count} submission(s)"
    if failed_files:
        message += f" (Failed to delete {len(failed_files)} file(s))"

    return {
        "message": message,
        "deleted_count": deleted_count,
        "failed_files": failed_files
    }
