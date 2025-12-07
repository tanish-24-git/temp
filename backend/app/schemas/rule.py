"""
Pydantic schemas for Rule model - Phase 2.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class RuleBase(BaseModel):
    """Base schema for Rule."""
    category: str = Field(..., description="Rule category: irdai, brand, or seo")
    rule_text: str = Field(..., min_length=10, description="Detailed rule description")
    severity: str = Field(..., description="Rule severity: critical, high, medium, or low")
    keywords: List[str] = Field(..., min_items=1, description="Keywords that trigger this rule")
    pattern: Optional[str] = Field(None, max_length=1000, description="Optional regex pattern")
    points_deduction: Decimal = Field(
        default=Decimal("-5.00"),
        description="Point deduction value (negative number)"
    )
    is_active: bool = Field(default=True, description="Whether rule is active")

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


class RuleCreate(RuleBase):
    """Schema for creating a new rule."""
    pass


class RuleUpdate(BaseModel):
    """Schema for updating an existing rule (all fields optional)."""
    rule_text: Optional[str] = Field(None, min_length=10)
    severity: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    pattern: Optional[str] = None
    points_deduction: Optional[Decimal] = None
    is_active: Optional[bool] = None

    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            allowed = ['irdai', 'brand', 'seo']
            if v not in allowed:
                raise ValueError(f"Category must be one of {allowed}")
        return v

    @validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            allowed = ['critical', 'high', 'medium', 'low']
            if v not in allowed:
                raise ValueError(f"Severity must be one of {allowed}")
        return v

    @validator('points_deduction')
    def validate_points_deduction(cls, v):
        if v is not None:
            if v > 0:
                raise ValueError("Points deduction must be negative or zero")
            if v < -50:
                raise ValueError("Points deduction cannot be less than -50")
        return v


class RuleResponse(RuleBase):
    """Schema for rule in API responses."""
    id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """Schema for paginated rule list."""
    rules: List[RuleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RuleGenerationRequest(BaseModel):
    """Schema for document upload to generate rules."""
    document_title: str = Field(..., min_length=1, max_length=255)


class RuleGenerationResponse(BaseModel):
    """Schema for rule generation result."""
    success: bool
    rules_created: int
    rules_failed: int
    rules: List[dict]
    errors: List[str]
