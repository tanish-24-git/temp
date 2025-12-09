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
            "overall": max(0.0, min(100.0, round(overall_score, 2))),
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
        
        Handles combined categories like "irdai|brand" by checking if the 
        target category is contained in the violation's category string.
        
        IMPORTANT: Uses proportional deduction to prevent scores from going to 0
        when there are many violations.
        """
        base_score = 100.0

        # Filter violations for this category (handles | separated categories)
        category_violations = []
        for v in violations:
            v_category = v.get("category", "")
            # Check if category matches exactly or is part of a combined category
            if category == v_category or category in v_category.split("|"):
                category_violations.append(v)

        if not category_violations:
            logger.debug(f"Category {category}: No violations, returning 100")
            return 100.0

        # Calculate total deduction
        total_deduction = 0
        for violation in category_violations:
            deduction = violation.get("points_deduction", 0)
            total_deduction += deduction
            logger.debug(f"Category {category}: +{deduction} points (severity={violation.get('severity')})")

        logger.info(f"Category {category}: {len(category_violations)} violations, total deduction={total_deduction}")

        # Apply deduction with scaling to prevent zero scores
        # If total deduction > 100, scale it down to max 95 (leave at least 5 points)
        if total_deduction > 100:
            # Use logarithmic scaling for very high deductions
            # This ensures even with 1000 points of violations, score doesn't hit 0
            scaled_deduction = 95 * (1 - (1 / (1 + total_deduction / 100)))
            logger.info(f"Category {category}: Scaled {total_deduction} → {scaled_deduction:.2f}")
            base_score -= scaled_deduction
        else:
            base_score -= total_deduction

        # Ensure score doesn't go below 0 or above 100
        final_score = max(0.0, min(100.0, base_score))
        logger.info(f"Category {category}: Final score = {final_score:.2f}")
        return final_score

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


scoring_service = ScoringService()
