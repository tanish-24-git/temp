from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ...database import get_db
from ...models.submission import Submission
from ...models.compliance_check import ComplianceCheck
from ...schemas.submission import SubmissionResponse
from ...schemas.dashboard import (
    ComplianceTrendsResponse,
    ViolationsHeatmapResponse,
    TopViolationResponse
)
from ...services.dashboard_service import dashboard_service

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


@router.get("/trends", response_model=ComplianceTrendsResponse)
def get_compliance_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get compliance score trends for the last N days.
    
    Returns daily aggregated scores with dates, scores, and counts.
    Uses date-based bucketing for consistent time-axis visualization.
    
    Args:
        days: Number of days to look back (default 30)
        db: Database session
        
    Returns:
        ComplianceTrendsResponse with dates, scores, and counts arrays
    """
    return dashboard_service.get_compliance_trends(db, days)


@router.get("/violations-heatmap", response_model=ViolationsHeatmapResponse)
def get_violations_heatmap(db: Session = Depends(get_db)):
    """Get violation distribution by category and severity.
    
    Returns pivoted data in ApexCharts-ready format with:
    - series: List of severity levels with counts per category
    - categories: List of category names (IRDAI, Brand, SEO)
    
    Returns:
        ViolationsHeatmapResponse ready for ApexCharts heatmap
    """
    return dashboard_service.get_violations_heatmap(db)


@router.get("/top-violations", response_model=List[TopViolationResponse])
def get_top_violations(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get most frequently occurring violations.
    
    Groups violations by description, category, and severity,
    counts occurrences, and returns the top N violations.
    
    Args:
        limit: Maximum number of violations to return (default 5)
        db: Database session
        
    Returns:
        List of top violations with description, count, severity, and category
    """
    return dashboard_service.get_top_violations(db, limit)
