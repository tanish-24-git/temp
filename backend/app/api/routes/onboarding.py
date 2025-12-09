"""Onboarding API Routes

Endpoints for user onboarding and auto rule generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
import logging

from ...database import get_db
from ...models.user import User
from ...models.user_config import UserConfig
from ...services.onboarding_service import onboarding_service

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])
logger = logging.getLogger(__name__)


# === Schemas ===

class OnboardingRequest(BaseModel):
    """User onboarding input."""
    user_id: UUID
    industry: str = Field(..., description="Industry name (e.g., 'insurance', 'healthcare')")
    brand_name: str = Field(..., description="Company/brand name")
    brand_guidelines: Optional[str] = Field(None, description="Optional brand guidelines text")
    analysis_scope: List[str] = Field(
        default=["regulatory", "brand", "seo"],
        description="Analysis categories to enable"
    )
    region: str = Field(default="India", description="Geographic region for regulations")


class OnboardingResponse(BaseModel):
    """Onboarding completion response."""
    success: bool
    config_id: UUID
    rules_generated: int
    by_category: dict
    sources_used: List[str]
    message: str


class ConfigResponse(BaseModel):
    """User configuration response."""
    id: UUID
    user_id: UUID
    industry: Optional[str]
    brand_name: Optional[str]
    analysis_scope: List[str]
    onboarding_completed: bool


# === Endpoints ===

@router.post("/start", response_model=OnboardingResponse)
async def start_onboarding(
    request: OnboardingRequest,
    db: Session = Depends(get_db)
):
    """
    Complete user onboarding and generate initial rules.
    
    **Workflow**:
    1. Save user config (industry, brand, scope)
    2. Search for industry regulations (API + RAG fallback)
    3. Generate compliance rules via Ollama
    4. Store rules in database
    5. Return summary
    
    **Example**:
    ```json
    {
      "user_id": "uuid",
      "industry": "insurance",
      "brand_name": "SecureLife Insurance",
      "analysis_scope": ["regulatory", "brand", "seo"]
    }
    ```
    """
    try:
        # Verify user exists
        user = db.query(User).filter_by(id=request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )
        
        logger.info(f"Starting onboarding for user {request.user_id}, industry: {request.industry}")
        
        # Complete onboarding
        result = await onboarding_service.complete_onboarding(
            user_id=request.user_id,
            industry=request.industry,
            brand_name=request.brand_name,
            brand_guidelines=request.brand_guidelines or "",
            analysis_scope=request.analysis_scope,
            db=db
        )
        
        # Get config ID
        config = db.query(UserConfig).filter_by(user_id=request.user_id).first()
        
        return OnboardingResponse(
            success=result["success"],
            config_id=config.id,
            rules_generated=result["rules_generated"],
            by_category=result["by_category"],
            sources_used=result["sources_used"],
            message=f"Onboarding complete! Generated {result['rules_generated']} rules."
        )
        
    except Exception as e:
        logger.error(f"Onboarding failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Onboarding failed: {str(e)}"
        )


@router.get("/{user_id}/config", response_model=ConfigResponse)
async def get_user_config(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get user configuration.
    
    Returns user's onboarding data and preferences.
    """
    config = db.query(UserConfig).filter_by(user_id=user_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User config not found. Complete onboarding first."
        )
    
    return ConfigResponse(
        id=config.id,
        user_id=config.user_id,
        industry=config.industry,
        brand_name=config.brand_name,
        analysis_scope=config.analysis_scope or [],
        onboarding_completed=config.onboarding_completed
    )


@router.put("/{user_id}/config")
async def update_user_config(
    user_id: UUID,
    industry: Optional[str] = None,
    brand_name: Optional[str] = None,
    analysis_scope: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Update user configuration.
    
    Allows users to modify their preferences after onboarding.
    """
    config = db.query(UserConfig).filter_by(user_id=user_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User config not found"
        )
    
    # Update fields if provided
    if industry:
        config.industry = industry
    if brand_name:
        config.brand_name = brand_name
    if analysis_scope:
        config.analysis_scope = analysis_scope
    
    db.commit()
    db.refresh(config)
    
    return {
        "success": True,
        "message": "Config updated successfully",
        "config": config.to_dict()
    }


@router.delete("/{user_id}/config/reset")
async def reset_onboarding(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Reset onboarding status.
    
    Allows user to go through onboarding again.
    Does NOT delete generated rules.
    """
    config = db.query(UserConfig).filter_by(user_id=user_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User config not found"
        )
    
    config.onboarding_completed = False
    db.commit()
    
    return {
        "success": True,
        "message": "Onboarding reset. User can complete onboarding again."
    }
