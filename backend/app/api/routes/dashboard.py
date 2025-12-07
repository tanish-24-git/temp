from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ...database import get_db
from ...models.submission import Submission
from ...models.compliance_check import ComplianceCheck
from ...schemas.submission import SubmissionResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_submissions = db.query(func.count(Submission.id)).scalar()
    pending_count = db.query(func.count(Submission.id)).filter(
        Submission.status == "pending"
    ).scalar()

    avg_score = db.query(func.avg(ComplianceCheck.overall_score)).scalar()

    flagged_count = db.query(func.count(ComplianceCheck.id)).filter(
        ComplianceCheck.status == "flagged"
    ).scalar()

    return {
        "total_submissions": total_submissions or 0,
        "pending_count": pending_count or 0,
        "avg_compliance_score": round(float(avg_score or 0), 2),
        "flagged_count": flagged_count or 0
    }


@router.get("/recent", response_model=List[SubmissionResponse])
def get_recent_submissions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent submissions."""
    submissions = db.query(Submission).order_by(
        Submission.submitted_at.desc()
    ).limit(limit).all()

    return submissions
