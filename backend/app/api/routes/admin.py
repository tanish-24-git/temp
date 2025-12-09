"""
Admin API routes for Phase 2 - Rule Management.

Super admin endpoints for dynamic rule generation and management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import os
import tempfile
import logging

from ...models.user import User
from ...models.rule import Rule
from ...schemas.rule import (
    RuleResponse,
    RuleCreate,
    RuleUpdate,
    RuleListResponse,
    RuleGenerationResponse
)
from ...schemas.rule_preview import (
    RulePreviewResponse,
    RuleRefineRequest,
    RuleRefineResponse,
    RuleBulkSubmitRequest,
    RuleBulkSubmitResponse,
    DraftRule
)
from ...services.rule_generator_service import rule_generator_service
from ..deps import get_db_session, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post(
    "/rules/generate",
    response_model=RuleGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate rules from uploaded document"
)
async def generate_rules_from_document(
    file: UploadFile = File(..., description="Compliance document (PDF, DOCX, HTML, MD)"),
    document_title: str = Form(..., description="Document title/name"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Generate compliance rules from an uploaded regulatory document.

    **Requires**: super_admin role

    **Process**:
    1. Upload document (PDF, DOCX, HTML, or Markdown)
    2. Parse document content
    3. Send to Ollama LLM for rule extraction
    4. Validate extracted rules
    5. Store rules in database

    **Returns**: Summary with created rules count and details
    """
    logger.info(f"Rule generation request from user {current_user.id}: {document_title}")

    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.html', '.htm', '.md', '.markdown'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    # Map file extension to content type
    content_type_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.html': 'html',
        '.htm': 'html',
        '.md': 'markdown',
        '.markdown': 'markdown'
    }
    content_type = content_type_map.get(file_ext, 'html')

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Saved uploaded file to: {temp_file_path}")

        # Generate rules
        result = await rule_generator_service.generate_rules_from_document(
            file_path=temp_file_path,
            content_type=content_type,
            document_title=document_title,
            created_by_user_id=current_user.id,
            db=db
        )

        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {str(e)}")

        return RuleGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Error generating rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate rules: {str(e)}"
        )


@router.post(
    "/rules/preview",
    response_model=RulePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview rules from document (no save)"
)
async def preview_rules_from_document(
    file: UploadFile = File(..., description="Compliance document (PDF, DOCX, HTML, MD)"),
    document_title: str = Form(..., description="Document title/name"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Generate compliance rules from document for PREVIEW without saving.

    **Requires**: super_admin role

    **Process**:
    1. Upload document (PDF, DOCX, HTML, or Markdown)
    2. Parse document content
    3. Send to Ollama LLM for rule extraction
    4. Return draft rules for user review/editing
    5. NO database save - user must explicitly submit approved rules

    **Returns**: List of draft rules for review and editing
    """
    logger.info(f"Rule preview request from user {current_user.id}: {document_title}")

    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.html', '.htm', '.md', '.markdown'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    # Map file extension to content type
    content_type_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.html': 'html',
        '.htm': 'html',
        '.md': 'markdown',
        '.markdown': 'markdown'
    }
    content_type = content_type_map.get(file_ext, 'html')

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Saved uploaded file for preview to: {temp_file_path}")

        # Generate preview (no save)
        result = await rule_generator_service.preview_rules_from_document(
            file_path=temp_file_path,
            content_type=content_type,
            document_title=document_title,
            created_by_user_id=current_user.id,
            db=db
        )

        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {str(e)}")

        return RulePreviewResponse(**result)

    except Exception as e:
        logger.error(f"Error generating rule preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate rule preview: {str(e)}"
        )


@router.post(
    "/rules/refine",
    response_model=RuleRefineResponse,
    summary="Refine a draft rule using AI"
)
async def refine_rule_with_ai(
    request: RuleRefineRequest,
    current_user: User = Depends(require_super_admin)
):
    """
    Use AI to refine a draft rule based on user instructions.

    **Requires**: super_admin role

    **Use cases**:
    - Make rule more specific
    - Improve clarity
    - Add more actionable language
    - Suggest better keywords

    **Returns**: Refined rule text and updated keywords
    """
    logger.info(f"Rule refinement request from user {current_user.id}")

    try:
        result = await rule_generator_service.refine_rule_with_ai(
            rule_text=request.rule_text,
            refinement_instruction=request.refinement_instruction,
            category=request.category,
            severity=request.severity
        )

        return RuleRefineResponse(**result)

    except Exception as e:
        logger.error(f"Error refining rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine rule: {str(e)}"
        )


@router.post(
    "/rules/bulk-submit",
    response_model=RuleBulkSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save approved draft rules to database"
)
async def bulk_submit_rules(
    request: RuleBulkSubmitRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Save approved draft rules to the database.

    **Requires**: super_admin role

    **Process**:
    1. Receives list of approved draft rules from preview
    2. Validates each rule
    3. Saves to database
    4. Returns list of created rule IDs

    **Note**: Only rules with is_approved=True will be saved
    """
    logger.info(f"Bulk submit request from user {current_user.id}: {len(request.approved_rules)} rules")

    result = {
        "success": False,
        "rules_created": 0,
        "rules_failed": 0,
        "created_rule_ids": [],
        "errors": []
    }

    approved_rules = [r for r in request.approved_rules if r.is_approved]
    
    if not approved_rules:
        result["errors"].append("No approved rules to save")
        return RuleBulkSubmitResponse(**result)

    try:
        for draft in approved_rules:
            try:
                new_rule = Rule(
                    category=draft.category,
                    rule_text=draft.rule_text,
                    severity=draft.severity,
                    keywords=draft.keywords,
                    pattern=draft.pattern,
                    points_deduction=float(draft.points_deduction),
                    is_active=True,
                    created_by=current_user.id
                )

                db.add(new_rule)
                db.flush()

                result["rules_created"] += 1
                result["created_rule_ids"].append(str(new_rule.id))
                logger.info(f"Created rule from preview: {new_rule.category} - {new_rule.severity}")

            except Exception as e:
                result["rules_failed"] += 1
                result["errors"].append(f"Failed to save rule: {str(e)}")
                logger.error(f"Error saving rule from preview: {str(e)}")

        db.commit()
        result["success"] = result["rules_created"] > 0

        logger.info(
            f"Bulk submit complete: {result['rules_created']} created, "
            f"{result['rules_failed']} failed"
        )

        return RuleBulkSubmitResponse(**result)

    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk submit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save rules: {str(e)}"
        )


@router.get(
    "/rules",
    response_model=RuleListResponse,
    summary="List all rules with pagination"
)
async def list_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category (irdai, brand, seo)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in rule text"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Get paginated list of all compliance rules.

    **Requires**: super_admin role

    **Filters**:
    - category: irdai, brand, or seo
    - severity: critical, high, medium, or low
    - is_active: true or false
    - search: Text search in rule_text

    **Pagination**: Uses page and page_size parameters
    """
    # Build query
    query = db.query(Rule)

    # Apply filters
    if category:
        query = query.filter(Rule.category == category)
    if severity:
        query = query.filter(Rule.severity == severity)
    if is_active is not None:
        query = query.filter(Rule.is_active == is_active)
    if search:
        query = query.filter(Rule.rule_text.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Get paginated rules
    rules = query.order_by(Rule.created_at.desc()).offset(offset).limit(page_size).all()

    return RuleListResponse(
        rules=[RuleResponse.from_orm(rule) for rule in rules],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Get single rule by ID"
)
async def get_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed information about a specific rule.

    **Requires**: super_admin role
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID {rule_id} not found"
        )

    return RuleResponse.from_orm(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Update an existing rule"
)
async def update_rule(
    rule_id: uuid.UUID,
    rule_update: RuleUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Update an existing compliance rule.

    **Requires**: super_admin role

    **Updatable fields**:
    - rule_text
    - severity
    - category
    - keywords
    - pattern
    - points_deduction
    - is_active
    """
    result = await rule_generator_service.regenerate_rule(
        rule_id=rule_id,
        new_rule_data=rule_update.dict(exclude_unset=True),
        updated_by_user_id=current_user.id,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to update rule")
        )

    # Fetch updated rule
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    return RuleResponse.from_orm(rule)


@router.delete(
    "/rules",
    summary="Delete (deactivate) all rules"
)
async def delete_all_rules(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Soft delete all rules by setting is_active to False.

    **Requires**: super_admin role

    **Note**: Rules are soft-deleted to preserve historical compliance data.
    """
    try:
        # Get count of active rules before deletion
        active_count = db.query(Rule).filter(Rule.is_active == True).count()
        
        # Soft delete all active rules
        db.query(Rule).filter(Rule.is_active == True).update(
            {"is_active": False},
            synchronize_session=False
        )
        db.commit()
        
        logger.info(f"User {current_user.id} soft-deleted {active_count} rules")
        
        return {
            "message": f"Successfully deactivated {active_count} rule(s)",
            "deactivated_count": active_count
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting all rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rules: {str(e)}"
        )


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (deactivate) a rule"
)
async def delete_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Soft delete a rule by setting is_active to False.

    **Requires**: super_admin role

    **Note**: Rules are soft-deleted to preserve historical compliance data.
    """
    result = await rule_generator_service.delete_rule(
        rule_id=rule_id,
        deleted_by_user_id=current_user.id,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to delete rule")
        )

    return None



@router.post(
    "/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rule manually"
)
async def create_rule_manually(
    rule: RuleCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Manually create a new compliance rule.

    **Requires**: super_admin role

    **Alternative to document upload**: Create rules directly via API.
    """
    try:
        new_rule = Rule(
            category=rule.category,
            rule_text=rule.rule_text,
            severity=rule.severity,
            keywords=rule.keywords,
            pattern=rule.pattern,
            points_deduction=float(rule.points_deduction),
            is_active=rule.is_active,
            created_by=current_user.id
        )

        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)

        return RuleResponse.from_orm(new_rule)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}"
        )


@router.get(
    "/rules/stats/summary",
    summary="Get rule statistics summary"
)
async def get_rule_stats(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db_session)
):
    """
    Get summary statistics about rules.

    **Requires**: super_admin role

    **Returns**:
    - Total rules count
    - Counts by category
    - Counts by severity
    - Active vs inactive counts
    """
    total = db.query(func.count(Rule.id)).scalar()
    active_count = db.query(func.count(Rule.id)).filter(Rule.is_active == True).scalar()

    # Count by category
    category_counts = {}
    for category in ['irdai', 'brand', 'seo']:
        count = db.query(func.count(Rule.id)).filter(Rule.category == category).scalar()
        category_counts[category] = count

    # Count by severity
    severity_counts = {}
    for severity in ['critical', 'high', 'medium', 'low']:
        count = db.query(func.count(Rule.id)).filter(Rule.severity == severity).scalar()
        severity_counts[severity] = count

    return {
        "total_rules": total,
        "active_rules": active_count,
        "inactive_rules": total - active_count,
        "by_category": category_counts,
        "by_severity": severity_counts
    }
