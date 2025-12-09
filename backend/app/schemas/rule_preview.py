"""
Pydantic schemas for Rule Preview workflow - Phase 2.

Draft rules for review before saving and AI refinement.
"""

from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import uuid


class DraftRule(BaseModel):
    """Draft rule object before saving to database."""
    temp_id: str = Field(..., description="Temporary ID for frontend tracking")
    category: str = Field(..., description="Rule category: irdai, brand, or seo")
    rule_text: str = Field(..., min_length=10, description="Detailed rule description")
    severity: str = Field(..., description="Rule severity: critical, high, medium, or low")
    keywords: List[str] = Field(..., min_items=1, description="Keywords that trigger this rule")
    pattern: Optional[str] = Field(None, max_length=1000, description="Optional regex pattern")
    points_deduction: Decimal = Field(
        default=Decimal("-5.00"),
        description="Point deduction value (negative number)"
    )
    is_approved: bool = Field(default=True, description="Whether user has approved this rule")

    @validator('category')
    def validate_category(cls, v):
        allowed = ['irdai', 'brand', 'seo']
        if v not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v

    @validator('severity')
    def validate_severity(cls, v):
        allowed = ['critical', 'high', 'medium', 'low']
        if v not in allowed:
            raise ValueError(f"Severity must be one of {allowed}")
        return v

    @validator('points_deduction')
    def validate_points_deduction(cls, v):
        if v > 0:
            raise ValueError("Points deduction must be negative or zero")
        if v < -50:
            raise ValueError("Points deduction cannot be less than -50")
        return v


class RulePreviewResponse(BaseModel):
    """Response for rule preview generation (before saving)."""
    success: bool
    document_title: str
    draft_rules: List[DraftRule]
    total_extracted: int
    errors: List[str]


class RuleRefineRequest(BaseModel):
    """Request to refine a draft rule using AI."""
    rule_text: str = Field(..., description="Current rule text to refine")
    refinement_instruction: str = Field(
        default="Make this rule more specific and actionable",
        description="How to refine the rule"
    )
    category: str = Field(..., description="Rule category for context")
    severity: str = Field(..., description="Rule severity for context")


class RuleRefineResponse(BaseModel):
    """Response from AI rule refinement."""
    success: bool
    original_text: str
    refined_text: str
    refined_keywords: List[str]
    error: Optional[str] = None


class RuleBulkSubmitRequest(BaseModel):
    """Request to save approved draft rules to database."""
    document_title: str = Field(..., description="Source document title")
    approved_rules: List[DraftRule] = Field(..., description="List of approved draft rules")


class RuleBulkSubmitResponse(BaseModel):
    """Response after saving approved rules."""
    success: bool
    rules_created: int
    rules_failed: int
    created_rule_ids: List[str]
    errors: List[str]
