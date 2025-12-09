from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class ViolationResponse(BaseModel):
    id: uuid.UUID
    severity: str
    category: str
    description: str
    location: str
    current_text: str
    suggested_fix: str
    is_auto_fixable: bool

    class Config:
        from_attributes = True


class ComplianceCheckResponse(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    overall_score: float
    irdai_score: float
    brand_score: float
    seo_score: float
    status: str
    grade: str
    ai_summary: str
    check_date: datetime
    has_deep_analysis: bool = False
    violations: List[ViolationResponse] = []

    class Config:
        from_attributes = True
