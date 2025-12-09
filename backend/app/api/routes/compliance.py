from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
import json
import asyncio
from ...database import get_db
from ...models.compliance_check import ComplianceCheck
from ...models.violation import Violation
from ...models.submission import Submission
from ...models.rule import Rule
from ...models.deep_analysis import DeepAnalysis
from ...schemas.compliance import ComplianceCheckResponse, ViolationResponse
from ...schemas.deep_analysis import (
    DeepAnalysisRequest,
    DeepAnalysisResponse,
    SeverityWeights
)
from ...services.deep_analysis_service import deep_analysis_service

logger = logging.getLogger(__name__)

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
        has_deep_analysis=True if check.deep_analysis else False,
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


# =============================================================================
# DEEP COMPLIANCE RESEARCH MODE ENDPOINTS
# =============================================================================

@router.post(
    "/{submission_id}/deep-analyze",
    response_model=DeepAnalysisResponse,
    summary="Run deep line-by-line compliance analysis"
)
async def run_deep_analysis(
    submission_id: uuid.UUID,
    request: DeepAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Execute granular line-by-line compliance analysis with custom severity weights.
    
    **Deep Compliance Research Mode**
    
    This endpoint triggers a detailed analysis where:
    1. Document is segmented into individual lines
    2. Each line is analyzed for rule violations
    3. Scores are calculated using user-defined severity multipliers
    4. All results are persisted for audit trail
    
    **Governance Features:**
    - `severity_config_snapshot`: Exact weights used are stored
    - `rule_impact_breakdown`: Detailed ledger of all deductions
    
    **Weights Range:** 0.0 to 3.0
    - 0.0 = Ignore violations of this severity
    - 1.0 = Standard weight
    - 2.0+ = Harsh penalties
    """
    logger.info(f"Deep analysis requested for submission {submission_id}")
    
    try:
        result = await deep_analysis_service.run_deep_analysis(
            submission_id=submission_id,
            severity_weights=request.severity_weights,
            db=db
        )
        return DeepAnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Deep analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Deep analysis failed: {str(e)}"
        )


@router.get(
    "/{submission_id}/deep-results",
    response_model=DeepAnalysisResponse,
    summary="Get deep analysis results"
)
async def get_deep_analysis_results(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve previously computed deep analysis results.
    
    Returns the line-by-line analysis including:
    - Individual line scores
    - Relevance context for each line
    - Detailed rule impact breakdown
    - Severity configuration used (audit snapshot)
    """
    result = await deep_analysis_service.get_deep_analysis_results(
        submission_id=submission_id,
        db=db
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No deep analysis found for this submission. Run deep-analyze first."
        )
    
    return DeepAnalysisResponse(**result)


@router.get(
    "/{submission_id}/deep-analyze/presets",
    summary="Get severity weight presets"
)
async def get_severity_presets():
    """
    Get predefined severity weight presets for quick configuration.
    
    Available presets:
    - **strict**: Harsh penalties for all violations
    - **balanced**: Standard weighting
    - **lenient**: Reduced penalties, good for initial review
    """
    return {
        "presets": {
            "strict": {
                "critical": 2.0,
                "high": 1.5,
                "medium": 1.0,
                "low": 0.5,
                "description": "Harsh penalties - suitable for final review"
            },
            "balanced": {
                "critical": 1.5,
                "high": 1.0,
                "medium": 0.5,
                "low": 0.2,
                "description": "Standard weighting - recommended default"
            },
            "lenient": {
                "critical": 1.0,
                "high": 0.5,
                "medium": 0.2,
                "low": 0.1,
                "description": "Reduced penalties - good for initial drafts"
            }
        }
    }


@router.post(
    "/{submission_id}/deep-analyze/stream",
    summary="Stream deep analysis progress with live updates"
)
async def stream_deep_analysis(
    submission_id: uuid.UUID,
    request: DeepAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Stream real-time progress during deep analysis.
    
    Returns Server-Sent Events (SSE) with:
    - progress: Current progress percentage
    - current_line: The line being analyzed
    - last_result: The last classified chunk with score
    - status: 'processing', 'complete', 'error'
    """
    
    async def generate_events():
        try:
            # Get submission
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if not submission:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Submission not found'})}\n\n"
                return
            
            # Get check
            check = db.query(ComplianceCheck).filter(
                ComplianceCheck.submission_id == submission_id
            ).first()
            
            if not check:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Compliance check not found'})}\n\n"
                return
            
            # Get active rules
            active_rules = db.query(Rule).filter(Rule.is_active == True).all()
            
            # Segment document
            content = submission.original_content or ""
            segments = deep_analysis_service.segment_document(content)
            total = len(segments)
            
            if total == 0:
                yield f"data: {json.dumps({'status': 'complete', 'message': 'No content to analyze', 'total_lines': 0})}\n\n"
                return
            
            severity_weights = request.severity_weights
            config_snapshot = severity_weights.model_dump()
            results = []
            
             # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'total_lines': total, 'document_title': submission.title})}\n\n"
            await asyncio.sleep(0.1)

            # Create initial record with 'processing' status
            from ...models.deep_analysis import DeepAnalysis

             # Create snapshot of severity config used
            config_snapshot = {
                "critical": request.severity_weights.critical,
                "high": request.severity_weights.high,
                "medium": request.severity_weights.medium,
                "low": request.severity_weights.low
            }

            # Delete existing
            db.query(DeepAnalysis).filter(DeepAnalysis.check_id == check.id).delete()
            
            # Create record
            deep_record = DeepAnalysis(
                check_id=check.id,
                total_lines=total,
                document_title=submission.title,
                severity_config_snapshot=config_snapshot,
                analysis_data=[],
                status='processing'
            )
            db.add(deep_record)
            db.commit() # Commit to make visible
            db.refresh(deep_record)
            
            # Process each line
            for i, segment in enumerate(segments):
                # Send progress update
                progress = {
                    'status': 'processing',
                    'progress': round((i / total) * 100, 1),
                    'current_index': i + 1,
                    'total_lines': total,
                    'current_line': {
                        'line_number': segment['line_number'],
                        'content': segment['line_content'][:100] + ('...' if len(segment['line_content']) > 100 else '')
                    }
                }
                yield f"data: {json.dumps(progress)}\n\n"
                
                # AI: Detect violations
                ai_result = await deep_analysis_service.detect_violations_with_ai(
                    line_content=segment["line_content"],
                    line_number=segment["line_number"],
                    document_context=submission.title,
                    active_rules=active_rules
                )
                
                # Calculate score
                line_score, impacts = deep_analysis_service.calculate_line_score(
                    base_score=100.0,
                    violations=ai_result.get("violations", []),
                    severity_weights=severity_weights
                )
                
                # Build result
                line_result = {
                    "line_number": segment["line_number"],
                    "line_content": segment["line_content"],
                    "line_score": round(line_score, 2),
                    "relevance_context": ai_result.get("relevance_context", ""),
                    "rule_impacts": [imp.model_dump() for imp in impacts]
                }
                results.append(line_result)
                
                # Send the classified result
                classified = {
                    'status': 'classified',
                    'progress': round(((i + 1) / total) * 100, 1),
                    'current_index': i + 1,
                    'total_lines': total,
                    'last_result': {
                        'line_number': segment['line_number'],
                        'content': segment['line_content'][:150] + ('...' if len(segment['line_content']) > 150 else ''),
                        'score': round(line_score, 2),
                        'relevance_context': ai_result.get("relevance_context", "")[:200],
                        'violations_count': len(impacts)
                    }
                }
                yield f"data: {json.dumps(classified)}\n\n"
            
            # Save to database
            from decimal import Decimal
            
            # Phase 2: Update original ComplianceCheck with new Deep Analysis scores
            # 1. Collect all violations found during deep analysis
            all_violations = []
            for r in results:
                all_violations.extend(r.get("rule_impacts", []))
            
            # 2. Calculate new scores using ScoringService (standardized logic)
            # Import locally to avoid circular dependencies if any
            from ...services.scoring_service import ScoringService
            new_scores = ScoringService.calculate_scores(all_violations, db)
            
            # 3. Update the ComplianceCheck record
            check.overall_score = new_scores["overall"]
            check.irdai_score = new_scores["irdai"]
            check.brand_score = new_scores["brand"]
            check.seo_score = new_scores["seo"]
            check.grade = new_scores["grade"]
            check.status = new_scores["status"]
            
            # Log the update
            # logger.info(f"Updated ComplianceCheck {check.id} with Deep Analysis scores: {new_scores}")
            
            avg_score = sum(r["line_score"] for r in results) / len(results) if results else 0
            scores = [r["line_score"] for r in results] if results else [0]
            
            
            # Update record
            deep_record.average_score = Decimal(str(round(avg_score, 2)))
            deep_record.min_score = Decimal(str(round(min(scores), 2)))
            deep_record.max_score = Decimal(str(round(max(scores), 2)))
            deep_record.analysis_data = results
            deep_record.status = 'completed'

            db.add(deep_record)
            db.add(check)  # Ensure check update is tracked
            db.commit()
            
            # Send completion
            complete = {
                'status': 'complete',
                'progress': 100,
                'total_lines': total,
                'average_score': round(avg_score, 2),
                'min_score': min(scores),
                'max_score': max(scores)
            }
            yield f"data: {json.dumps(complete)}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            # Attempt to mark as failed
            try:
                # Need fresh session or rollback if transaction failed
                db.rollback()
                failed_check = db.query(ComplianceCheck).filter(ComplianceCheck.submission_id == submission_id).first()
                if failed_check:
                    failed_record = db.query(DeepAnalysis).filter(DeepAnalysis.check_id == failed_check.id).first()
                    if failed_record:
                        failed_record.status = 'failed'
                        db.commit()
            except:
                pass
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get(
    "/{submission_id}/deep-analysis/export",
    summary="Export deep analysis report as DOCX"
)
async def export_deep_analysis_report(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Generate and download a DOCX report for the deep compliance analysis.
    """
    try:
        # Get submission title
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(404, "Submission not found")
            
        # Get deep analysis results
        result = await deep_analysis_service.get_deep_analysis_results(
            submission_id=submission_id,
            db=db
        )
        
        if not result:
            raise HTTPException(404, "No deep analysis found. Run analysis first.")

        # Generate HTML (Inline to avoid import issues)
        # Build HTML content
        html_content = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            .stats-table th {{ background-color: #f8f9fa; }}
            .score-red {{ color: #c0392b; }}
            .score-green {{ color: #27ae60; }}
            .violation {{ margin-left: 20px; color: #555; }}
            .footer {{ margin-top: 50px; font-size: 0.8em; color: #7f8c8d; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
        </head>
        <body>
            <h1>Deep Compliance Analysis Report</h1>
            <p><strong>Document:</strong> {submission.title}</p>
            <p><strong>Analysis Status:</strong> {result.get('status', 'Completed').title()}</p>
            
            <h2>Executive Summary</h2>
            <table class="stats-table">
                <tr><th>Total Lines</th><th>Avg Score</th><th>Min Score</th><th>Max Score</th></tr>
                <tr>
                    <td>{result.get('total_lines', 0)}</td>
                    <td>{result.get('average_score', 0):.2f}</td>
                    <td>{result.get('min_score', 0):.2f}</td>
                    <td>{result.get('max_score', 0):.2f}</td>
                </tr>
            </table>

            <h2>Detailed Analysis</h2>
        """
        
        lines = result.get('lines', [])
        for line in lines:
            content = line.get('line_content', '').strip()
            if not content: continue
            score = line.get('line_score', 100)
            impacts = line.get('rule_impacts', [])
            score_class = "score-red" if score < 100 else "score-green"
            
            html_content += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #eee;">
                <p><strong>Line {line.get('line_number')}:</strong> {content}</p>
                <p>Score: <span class="{score_class}">{score:.2f}</span></p>
            """
            if impacts:
                html_content += "<ul>"
                for impact in impacts:
                    html_content += f"<li>[{impact.get('severity','').upper()}] {impact.get('violation_reason')}</li>"
                html_content += "</ul>"
            html_content += "</div>"
            
        html_content += "</body></html>"
        
        from datetime import datetime
        filename = f"Compliance_Deep_Analysis_{submission_id}_{datetime.now().strftime('%Y%m%d')}.html"
        
        from fastapi import Response
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.post(
    "/{submission_id}/deep-analysis/sync",
    summary="Sync Deep Analysis results to main Overview"
)
async def sync_deep_analysis_results(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Promote Deep Analysis results to the main Compliance Check.
    
    1. Updates ComplianceCheck.overall_score to match DeepAnalysis.average_score
    2. Replaces all Violations with those found in Deep Analysis
    3. Recalculates sub-scores (IRDAI, Brand, SEO) based on the new violations
    """
    # Get Deep Analysis
    deep_analysis = db.query(DeepAnalysis).join(ComplianceCheck).filter(
        ComplianceCheck.submission_id == submission_id
    ).first()
    
    if not deep_analysis:
        raise HTTPException(404, "Deep Analysis results not found")
        
    # Get Compliance Check
    check = deep_analysis.compliance_check
    if not check:
        raise HTTPException(404, "Compliance Check not found")
        
    try:
        # 1. Convert Deep Analysis impacts to Violations
        new_violations = []
        analysis_data = deep_analysis.analysis_data or []
        
        for line in analysis_data:
            impacts = line.get("rule_impacts", [])
            line_content = line.get("line_content", "")
            line_number = line.get("line_number")
            
            for impact in impacts:
                # Map RuleImpact to Violation
                # Use AI to match Deep Analysis violations to existing database rules
                from ...services.rule_matcher_service import rule_matcher_service
                
                violation_description = impact.get("violation_reason", "Violation detected via Deep Analysis")
                category = impact.get("category", "unknown")
                severity = impact.get("severity", "low")
                
                # Try to find matching rule using AI semantic matching
                matched_rule_id = await rule_matcher_service.match_violation_to_rule(
                    violation_description=violation_description,
                    category=category,
                    severity=severity,
                    db=db
                )
                
                violation_dict = {
                    "check_id": check.id,
                    "rule_id": matched_rule_id,  # AI-matched rule or None if no good match
                    "severity": severity,
                    "category": category,
                    "description": violation_description,
                    "location": f"Line {line_number}",
                    "current_text": line_content.strip(),
                    "suggested_fix": "Review compliance guidelines.",
                    "is_auto_fixable": False
                }
                new_violations.append(violation_dict)
        
        # 2. Delete existing violations
        db.query(Violation).filter(Violation.check_id == check.id).delete()
        
        # 3. Insert new violations
        for v_data in new_violations:
            db_violation = Violation(**v_data)
            db.add(db_violation)
            
        # 4. Update Scores
        # We explicitly set overall_score to Deep Analysis average to match user request
        check.overall_score = deep_analysis.average_score
        
        # Recalculate sub-scores using ScoringService on the NEW violations
        # This ensures sub-scores are consistent with the new violation set
        # We ignore the returned 'overall' from scoring service in favor of DA average
        from ...services.scoring_service import scoring_service
        
        try:
            logger.info(f"Calculating scores for {len(new_violations)} violations")
            logger.debug(f"Sample violation: {new_violations[0] if new_violations else 'None'}")
            
            # CRITICAL FIX: The scoring service expects actual Violation objects or dicts with proper structure
            # But new_violations is a list of dicts for insertion. We need to fetch the actual inserted violations.
            # However, we haven't inserted them yet! So we pass the dicts, and scoring service will handle them.
            scores = scoring_service.calculate_scores(new_violations, db)
            
            logger.info(f"Calculated scores: IRDAI={scores['irdai']}, Brand={scores['brand']}, SEO={scores['seo']}")
            
            check.irdai_score = scores["irdai"]
            check.brand_score = scores["brand"]
            check.seo_score = scores["seo"]
            check.grade = scores["grade"]
            check.status = scores["status"]
        except Exception as scoring_error:
            # If scoring fails (e.g., due to missing rules), use simple defaults
            logger.warning(f"Scoring service failed, using defaults: {str(scoring_error)}")
            violation_count = len(new_violations)
            check.irdai_score = max(0, 100 - (violation_count * 2))
            check.brand_score = max(0, 100 - (violation_count * 2))
            check.seo_score = max(0, 100 - (violation_count * 2))
            
            # Derive grade and status from overall score
            overall = float(check.overall_score)
            if overall >= 90:
                check.grade = "A"
                check.status = "passed"
            elif overall >= 80:
                check.grade = "B"
                check.status = "passed"
            elif overall >= 70:
                check.grade = "C"
                check.status = "flagged"
            elif overall >= 60:
                check.grade = "D"
                check.status = "flagged"
            else:
                check.grade = "F"
                check.status = "failed"
        
        check.ai_summary = "Updated with Deep Analysis findings."
        
        db.commit()
        
        return {"status": "success", "message": "Results synced to Overview"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(500, f"Sync failed: {str(e)}")
