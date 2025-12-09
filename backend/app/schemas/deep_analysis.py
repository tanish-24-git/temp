"""
Deep Analysis Pydantic Schemas

Schemas for the Deep Compliance Research Mode feature.
Includes request/response models for severity weights, line analysis,
and rule impact breakdown.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid


class SeverityWeights(BaseModel):
    """
    User-configurable severity multipliers for dynamic scoring.
    
    Range: 0.0 to 3.0
    - 0.0 = Ignore violations of this severity
    - 1.0 = Standard weight (no modification)
    - 2.0+ = Harsh penalties
    """
    critical: float = Field(default=1.5, ge=0.0, le=3.0, description="Weight for critical violations")
    high: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for high violations")
    medium: float = Field(default=0.5, ge=0.0, le=3.0, description="Weight for medium violations")
    low: float = Field(default=0.2, ge=0.0, le=3.0, description="Weight for low violations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "critical": 1.5,
                "high": 1.0,
                "medium": 0.5,
                "low": 0.2
            }
        }


class DeepAnalysisRequest(BaseModel):
    """Request payload to trigger deep line-by-line analysis."""
    severity_weights: SeverityWeights = Field(
        default_factory=SeverityWeights,
        description="Custom severity weights for this analysis run"
    )


class RuleImpact(BaseModel):
    """
    Detailed record of a single rule's impact on a line's score.
    This forms part of the audit trail (rule_impact_breakdown).
    """
    rule_id: str = Field(description="UUID of the violated rule")
    rule_text: str = Field(description="Text of the violated rule")
    category: str = Field(description="Rule category: irdai, brand, or seo")
    severity: str = Field(description="Rule severity: critical, high, medium, low")
    base_deduction: float = Field(description="Standard deduction before weight applied")
    weight_multiplier: float = Field(description="User's severity weight for this level")
    weighted_deduction: float = Field(description="Final deduction = base * weight")
    violation_reason: str = Field(description="AI explanation of why the rule was violated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "123e4567-e89b-12d3-a456-426614174000",
                "rule_text": "All insurance advertisements must include IRDAI registration number",
                "category": "irdai",
                "severity": "critical",
                "base_deduction": -20.0,
                "weight_multiplier": 1.5,
                "weighted_deduction": -30.0,
                "violation_reason": "Missing IRDAI registration number in promotional content"
            }
        }


class LineAnalysisResult(BaseModel):
    """Analysis result for a single line/segment of the document."""
    id: Optional[str] = Field(default=None, description="UUID of the deep_analysis record")
    line_number: int = Field(description="Sequential line number in the document")
    line_content: str = Field(description="Raw text content of the line")
    line_score: float = Field(description="Compliance score for this line (0-100)")
    relevance_context: str = Field(
        default="",
        description="AI-generated context explaining what this line is relevant to"
    )
    rule_impacts: List[RuleImpact] = Field(
        default=[],
        description="Detailed breakdown of all rule impacts on this line"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc12345-...",
                "line_number": 5,
                "line_content": "Get 20% discount on all health insurance plans!",
                "line_score": 70.0,
                "relevance_context": "Marketing claim about pricing that requires regulatory validation",
                "rule_impacts": []
            }
        }


class DeepAnalysisResponse(BaseModel):
    """Complete response for a deep analysis run."""
    check_id: str = Field(description="UUID of the compliance check")
    submission_id: str = Field(description="UUID of the submission")
    document_title: str = Field(description="Title of the analyzed document")
    total_lines: int = Field(description="Total number of lines analyzed")
    average_score: float = Field(description="Average score across all lines")
    min_score: float = Field(description="Lowest line score")
    max_score: float = Field(description="Highest line score")
    severity_config: SeverityWeights = Field(
        description="Severity weights used for this analysis (audit snapshot)"
    )
    status: str = Field(
        default="completed",
        description="Status of the analysis: pending, processing, completed, failed"
    )
    lines: List[LineAnalysisResult] = Field(
        description="Line-by-line analysis results"
    )
    analysis_timestamp: Optional[str] = Field(
        default=None,
        description="When the analysis was performed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "check_id": "...",
                "submission_id": "...",
                "document_title": "Summer Insurance Promotion",
                "total_lines": 25,
                "average_score": 82.5,
                "min_score": 45.0,
                "max_score": 100.0,
                "severity_config": {"critical": 1.5, "high": 1.0, "medium": 0.5, "low": 0.2},
                "lines": [],
                "analysis_timestamp": "2025-12-07T12:00:00Z"
            }
        }


class DeepAnalysisSummary(BaseModel):
    """Summary statistics for deep analysis (used in listings)."""
    check_id: str
    submission_id: str
    total_lines: int
    average_score: float
    lines_with_violations: int
    severity_config: SeverityWeights
    created_at: str
