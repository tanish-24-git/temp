from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ScoringService:
    """Calculate compliance scores based on violations."""

    # Phase 2: Fallback weights (used only if DB rule not found)
    # Now these are positive values representing point deductions
    FALLBACK_WEIGHTS = {
        "critical": 20,  # Regulatory/safety critical
        "high": 10,      # Product accuracy
        "medium": 5,     # Style/branding
        "low": 2         # Minor issues
    }

    # Category weights for overall score
    CATEGORY_WEIGHTS = {
        "irdai": 0.50,   # 50% - Most important
        "brand": 0.30,   # 30%
        "seo": 0.20      # 20%
    }

    @staticmethod
    def calculate_scores(violations: List[Dict], db: Optional[Session] = None) -> Dict[str, float]:
        """
        Calculate compliance scores based on violations.

        Phase 2 Update: Now uses DB-stored points_deduction from rules table.
        If a violation has a rule_id, fetches the actual points_deduction value.
        Falls back to severity-based weights if rule not found.

        Args:
            violations: List of violation dictionaries
            db: Database session (optional, for Phase 2 rule-based scoring)

        Returns:
            {
                "overall": 85.5,
                "irdai": 90.0,
                "brand": 85.0,
                "seo": 80.0,
                "grade": "B",
                "status": "passed"
            }
        """
        # Phase 2: Enrich violations with DB-based point deductions
        enriched_violations = ScoringService._enrich_violations_with_points(violations, db)

        # Calculate category scores
        irdai_score = ScoringService._calculate_category_score(enriched_violations, "irdai")
        brand_score = ScoringService._calculate_category_score(enriched_violations, "brand")
        seo_score = ScoringService._calculate_category_score(enriched_violations, "seo")

        # Calculate weighted overall score
        overall_score = (
            irdai_score * ScoringService.CATEGORY_WEIGHTS["irdai"] +
            brand_score * ScoringService.CATEGORY_WEIGHTS["brand"] +
            seo_score * ScoringService.CATEGORY_WEIGHTS["seo"]
        )

        # Get grade
        grade = ScoringService._get_grade(overall_score)

        # Determine status
        status = ScoringService._get_status(enriched_violations, overall_score)

        return {
            "overall": round(overall_score, 2),
            "irdai": round(irdai_score, 2),
            "brand": round(brand_score, 2),
            "seo": round(seo_score, 2),
            "grade": grade,
            "status": status
        }

    @staticmethod
    def _enrich_violations_with_points(
        violations: List[Dict],
        db: Optional[Session] = None
    ) -> List[Dict]:
        """
        Phase 2: Enrich violations with DB-stored point deductions.

        For each violation with a rule_id, fetches the points_deduction from the database.
        Falls back to severity-based weights if rule not found or no DB session.

        Args:
            violations: List of violation dicts
            db: Optional database session

        Returns:
            List of violations with 'points_deduction' field added
        """
        if not db:
            # No DB session, use fallback weights
            for violation in violations:
                severity = violation.get("severity", "low")
                violation["points_deduction"] = ScoringService.FALLBACK_WEIGHTS.get(severity, 5)
            return violations

        # Import here to avoid circular dependency
        from ..models.rule import Rule

        enriched = []
        for violation in violations:
            # Try to get points from rule
            rule_id = violation.get("rule_id")
            points_deduction = None

            if rule_id:
                try:
                    rule = db.query(Rule).filter(Rule.id == rule_id).first()
                    if rule and rule.points_deduction:
                        # Convert to positive deduction value (DB stores negative)
                        points_deduction = abs(float(rule.points_deduction))
                        logger.debug(f"Using DB points for rule {rule_id}: {points_deduction}")
                except Exception as e:
                    logger.warning(f"Error fetching rule {rule_id}: {str(e)}")

            # Fallback to severity-based weight
            if points_deduction is None:
                severity = violation.get("severity", "low")
                points_deduction = ScoringService.FALLBACK_WEIGHTS.get(severity, 5)
                logger.debug(f"Using fallback points for {severity}: {points_deduction}")

            violation["points_deduction"] = points_deduction
            enriched.append(violation)

        return enriched

    @staticmethod
    def _calculate_category_score(violations: List[Dict], category: str) -> float:
        """
        Calculate score for a specific category.

        Phase 2 Update: Now uses the 'points_deduction' field from violations
        instead of looking up severity weights.
        """
        base_score = 100.0

        # Filter violations for this category
        category_violations = [v for v in violations if v.get("category") == category]

        # Deduct points using DB-stored values
        for violation in category_violations:
            deduction = violation.get("points_deduction", 0)
            base_score -= deduction
            logger.debug(f"Category {category}: Deducting {deduction} points")

        # Ensure score doesn't go below 0
        return max(0.0, base_score)

    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def _get_status(violations: List[Dict], overall_score: float) -> str:
        """Determine compliance status."""
        # Check for critical violations
        has_critical = any(v.get("severity") == "critical" for v in violations)

        if has_critical or overall_score < 60:
            return "failed"
        elif overall_score < 80:
            return "flagged"
        else:
            return "passed"


# ==============================================
# FEATURE 6: PRIORITY SCORING
# Helps sort violations by risk level
# WHY: Allows prioritization of violations based on both severity and confidence
#      so critical, high-confidence issues are addressed first
# ==============================================
SEVERITY_WEIGHTS = {
    "critical": 5,
    "high": 3,
    "medium": 2,
    "low": 1
}


def compute_priority(v: Dict) -> float:
    """
    Compute priority score for a violation.
    
    Args:
        v: Violation dictionary with 'severity' and 'confidence' fields
    
    Returns:
        Priority score (severity_weight × confidence)
    """
    severity = v.get("severity", "low")
    confidence = v.get("confidence", 0.5)
    weight = SEVERITY_WEIGHTS.get(severity, 1)
    return weight * confidence


scoring_service = ScoringService()
