"""
Deep Analysis Service - Deterministic Orchestrator

This service implements the Deep Compliance Research Mode using
Deterministic Orchestration pattern:

1. LLM (Ollama) - Violation detection + context generation ONLY
2. Python Logic - Score calculation + weight application (DETERMINISTIC)
3. Persistence - Full audit trail in deep_analysis table (SINGLE JSON)

Architecture ensures:
- Predictable, testable scoring logic
- Complete audit trail for governance
- Separation of AI inference from business rules
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.rule import Rule
from ..models.deep_analysis import DeepAnalysis
from ..models.compliance_check import ComplianceCheck
from ..models.submission import Submission
from ..schemas.deep_analysis import SeverityWeights, RuleImpact, LineAnalysisResult
from .ollama_service import ollama_service
from .content_retrieval_service import ContentRetrievalService

logger = logging.getLogger(__name__)

# Base deductions per severity level (from rule definitions)
BASE_DEDUCTIONS = {
    "critical": -20.0,
    "high": -10.0,
    "medium": -5.0,
    "low": -2.0
}


class DeepAnalysisService:
    """
    Orchestrates line-by-line compliance analysis using
    Deterministic Orchestration pattern.
    
    Key Principles:
    - LLM only identifies violations (non-deterministic)
    - Score calculation is pure Python (deterministic, auditable)
    - All results stored as SINGLE JSON document per submission
    """
    
    def segment_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Step 1: Segment document into analyzable lines.
        
        DETERMINISTIC - No AI involved.
        Splits content into meaningful segments for analysis.
        """
        if not content:
            return []
        
        lines = content.split('\n')
        segments = []
        
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Skip empty lines and very short lines
            if stripped and len(stripped) > 3:
                segments.append({
                    "line_number": i,
                    "line_content": stripped,
                    "original_line": line
                })
        
        logger.info(f"Document segmented into {len(segments)} analyzable lines")
        return segments
    
    async def detect_violations_with_ai(
        self,
        line_content: str,
        line_number: int,
        document_context: str,
        active_rules: List[Rule]
    ) -> Dict[str, Any]:
        """
        Step 2: Use AI for violation DETECTION only.
        
        The LLM's role is LIMITED to:
        - Identifying which rules are violated
        - Generating relevance context
        
        Returns structured JSON, NO scoring.
        """
        # Convert rules to dict format for prompt
        rules_data = [{
            "id": str(r.id),
            "category": r.category,
            "rule_text": r.rule_text,
            "severity": r.severity,
            "keywords": r.keywords or []
        } for r in active_rules]
        
        return await ollama_service.analyze_line_for_violations(
            line_content=line_content,
            line_number=line_number,
            document_context=document_context,
            rules=rules_data
        )
    
    def calculate_line_score(
        self,
        base_score: float,
        violations: List[Dict],
        severity_weights: SeverityWeights
    ) -> tuple[float, List[RuleImpact]]:
        """
        Step 3: DETERMINISTIC score calculation.
        
        NO AI INVOLVED - Pure Python logic for auditability.
        """
        score = base_score
        impacts = []
        
        # Get weights as dict for lookup
        weights_dict = severity_weights.model_dump()
        
        for violation in violations:
            severity = violation.get("severity", "low").lower()
            
            # Get base deduction for this severity
            base_deduction = BASE_DEDUCTIONS.get(severity, -2.0)
            
            # Get user's weight multiplier
            weight = weights_dict.get(severity, 1.0)
            
            # Calculate weighted deduction
            weighted_deduction = base_deduction * weight
            
            # Apply deduction to score
            score += weighted_deduction
            
            # Record in audit ledger
            impacts.append(RuleImpact(
                rule_id=violation.get("rule_id", "unknown"),
                rule_text=violation.get("rule_text", "Unknown rule"),
                category=violation.get("category", "unknown"),
                severity=severity,
                base_deduction=base_deduction,
                weight_multiplier=weight,
                weighted_deduction=weighted_deduction,
                violation_reason=violation.get("reason", "No reason provided")
            ))
        
        # Clamp score to valid range [0, 100]
        score = max(0.0, min(100.0, score))
        
        return score, impacts
    
    async def run_deep_analysis(
        self,
        submission_id: uuid.UUID,
        severity_weights: SeverityWeights,
        db: Session
    ) -> Dict[str, Any]:
        """
        Main orchestration: Execute full deep line-by-line analysis.
        
        Stores results as SINGLE JSON document per submission.
        """
        logger.info(f"Starting deep analysis for submission {submission_id}")
        
        # Get submission
        submission = db.query(Submission).filter(
            Submission.id == submission_id
        ).first()
        
        if not submission:
            raise ValueError(f"Submission not found: {submission_id}")
        
        # Get compliance check (must exist)
        check = db.query(ComplianceCheck).filter(
            ComplianceCheck.submission_id == submission_id
        ).first()
        
        if not check:
            raise ValueError(f"No compliance check found for submission: {submission_id}")
        
        # Get active rules
        active_rules = db.query(Rule).filter(Rule.is_active == True).all()
        logger.info(f"Found {len(active_rules)} active rules")
        
        # Step 1: Get chunks via ContentRetrievalService (CHUNK-AWARE)
        content_service = ContentRetrievalService(db)
        chunks = content_service.get_analyzable_content(submission_id)
        
        if not chunks:
            logger.warning("No content to analyze")
            return self._build_empty_response(check, submission, severity_weights)
        
        logger.info(f"Analyzing {len(chunks)} chunk(s) for deep analysis")
        
        # Store severity config snapshot
        config_snapshot = severity_weights.model_dump()
        
        results = []
        total_score = 0.0
        
        # Step 2 & 3: Analyze each chunk (AI + Deterministic scoring)
        for i, chunk in enumerate(chunks):
            logger.debug(f"Analyzing chunk {chunk.chunk_index + 1}/{len(chunks)}")
            
            # AI: Detect violations (non-deterministic)
            ai_result = await self.detect_violations_with_ai(
                line_content=chunk.text,
                line_number=chunk.chunk_index + 1,  # For prompt compatibility
                document_context=submission.title,
                active_rules=active_rules
            )
            
            # Python: Calculate score (DETERMINISTIC)
            chunk_score, impacts = self.calculate_line_score(
                base_score=100.0,
                violations=ai_result.get("violations", []),
                severity_weights=severity_weights
            )
            
            # Build chunk result (will be stored in JSON)
            # Store chunk_id for frontend mapping
            chunk_result = {
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "chunk_content": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,  # Preview
                "chunk_score": round(chunk_score, 2),
                "token_count": chunk.token_count,
                "metadata": chunk.metadata,  # Preserve source location info
                "relevance_context": ai_result.get("relevance_context", ""),
                "rule_impacts": [imp.model_dump() for imp in impacts]
            }
            results.append(chunk_result)
            total_score += chunk_score
        
        # Calculate summary stats
        avg_score = total_score / len(results) if results else 100.0
        scores = [r["chunk_score"] for r in results]
        min_score = min(scores) if scores else 100.0
        max_score = max(scores) if scores else 100.0
        
        # Delete existing analysis for this check (if any)
        db.query(DeepAnalysis).filter(DeepAnalysis.check_id == check.id).delete()
        
        # Create single record with all data
        deep_record = DeepAnalysis(
            check_id=check.id,
            total_lines=len(results),  # Field name kept for DB compatibility, but contains chunk count
            average_score=Decimal(str(round(avg_score, 2))),
            min_score=Decimal(str(round(min_score, 2))),
            max_score=Decimal(str(round(max_score, 2))),
            document_title=submission.title,
            severity_config_snapshot=config_snapshot,
            analysis_data=results  # All chunks as JSON array
        )
        db.add(deep_record)
        db.commit()
        
        logger.info(
            f"Deep analysis complete: {len(results)} chunk(s) stored as single JSON, "
            f"avg={avg_score:.2f}, min={min_score:.2f}, max={max_score:.2f}"
        )
        
        return deep_record.to_response_dict(str(submission_id))
    
    def _build_empty_response(
        self,
        check: ComplianceCheck,
        submission: Submission,
        severity_weights: SeverityWeights
    ) -> Dict[str, Any]:
        """Build response for empty documents."""
        return {
            "check_id": str(check.id),
            "submission_id": str(submission.id),
            "document_title": submission.title,
            "total_lines": 0,
            "average_score": 100.0,
            "min_score": 100.0,
            "max_score": 100.0,
            "severity_config": severity_weights.model_dump(),
            "lines": [],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_deep_analysis_results(
        self,
        submission_id: uuid.UUID,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve previously computed deep analysis results.
        
        Returns the single JSON document containing all analysis.
        """
        # Get check
        check = db.query(ComplianceCheck).filter(
            ComplianceCheck.submission_id == submission_id
        ).first()
        
        if not check:
            return None
        
        # Get deep analysis record (single record per check)
        record = db.query(DeepAnalysis).filter(
            DeepAnalysis.check_id == check.id
        ).first()
        
        if not record:
            return None
        
        return record.to_response_dict(str(submission_id))


# Singleton instance
deep_analysis_service = DeepAnalysisService()
