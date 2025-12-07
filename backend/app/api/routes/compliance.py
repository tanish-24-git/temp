from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from ...database import get_db
from ...models.compliance_check import ComplianceCheck
from ...models.violation import Violation
from ...schemas.compliance import ComplianceCheckResponse, ViolationResponse

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/{submission_id}", response_model=ComplianceCheckResponse)
def get_compliance_results(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get compliance check results for a submission."""
    check = db.query(ComplianceCheck).filter(
        ComplianceCheck.submission_id == submission_id
    ).first()

    if not check:
        raise HTTPException(404, "No compliance check found for this submission")

    # Load violations
    violations = db.query(Violation).filter(Violation.check_id == check.id).all()

    response = ComplianceCheckResponse(
        id=check.id,
        submission_id=check.submission_id,
        overall_score=float(check.overall_score),
        irdai_score=float(check.irdai_score),
        brand_score=float(check.brand_score),
        seo_score=float(check.seo_score),
        status=check.status,
        grade=check.grade,
        ai_summary=check.ai_summary,
        check_date=check.check_date,
        violations=[ViolationResponse.from_orm(v) for v in violations]
    )

    return response


@router.get("/{submission_id}/violations", response_model=List[ViolationResponse])
def get_violations(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get violations for a submission."""
    check = db.query(ComplianceCheck).filter(
        ComplianceCheck.submission_id == submission_id
    ).first()

    if not check:
        raise HTTPException(404, "No compliance check found")

    violations = db.query(Violation).filter(Violation.check_id == check.id).all()

    return violations
