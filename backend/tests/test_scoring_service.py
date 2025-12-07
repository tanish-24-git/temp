"""
Unit tests for scoring_service.py - Phase 2 DB-based scoring
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal

from app.services.scoring_service import ScoringService
from app.models.rule import Rule


class TestScoringServicePhase2:
    """Test Phase 2 DB-based scoring functionality."""

    def test_calculate_scores_without_db_uses_fallback(self):
        """Test that scoring works without DB session (fallback mode)."""
        violations = [
            {
                "category": "irdai",
                "severity": "critical",
                "description": "Test violation"
            },
            {
                "category": "brand",
                "severity": "high",
                "description": "Test violation 2"
            }
        ]

        scores = ScoringService.calculate_scores(violations, db=None)

        # Should use fallback weights: critical=-20, high=-10
        # IRDAI: 100 - 20 = 80
        # Brand: 100 - 10 = 90
        # SEO: 100 (no violations)
        # Overall: 80*0.5 + 90*0.3 + 100*0.2 = 40 + 27 + 20 = 87

        assert scores["irdai"] == 80.0
        assert scores["brand"] == 90.0
        assert scores["seo"] == 100.0
        assert scores["overall"] == 87.0
        assert scores["grade"] == "B"
        assert scores["status"] == "flagged"

    def test_calculate_scores_with_db_uses_rule_points(self):
        """Test that scoring uses DB rule points when available."""
        # Mock database session
        mock_db = Mock()

        # Create mock rules with custom point deductions
        mock_rule_1 = Mock(spec=Rule)
        mock_rule_1.id = "rule-1"
        mock_rule_1.points_deduction = Decimal("-25.00")  # Custom: -25 instead of standard -20

        mock_rule_2 = Mock(spec=Rule)
        mock_rule_2.id = "rule-2"
        mock_rule_2.points_deduction = Decimal("-15.00")  # Custom: -15 instead of standard -10

        # Setup mock DB query
        def mock_query_filter_first(rule_id):
            if rule_id == "rule-1":
                return mock_rule_1
            elif rule_id == "rule-2":
                return mock_rule_2
            return None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_rule_1,
            mock_rule_2
        ]

        violations = [
            {
                "category": "irdai",
                "severity": "critical",
                "description": "Test violation",
                "rule_id": "rule-1"
            },
            {
                "category": "brand",
                "severity": "high",
                "description": "Test violation 2",
                "rule_id": "rule-2"
            }
        ]

        scores = ScoringService.calculate_scores(violations, db=mock_db)

        # Should use DB points: -25 and -15
        # IRDAI: 100 - 25 = 75
        # Brand: 100 - 15 = 85
        # SEO: 100
        # Overall: 75*0.5 + 85*0.3 + 100*0.2 = 37.5 + 25.5 + 20 = 83

        assert scores["irdai"] == 75.0
        assert scores["brand"] == 85.0
        assert scores["seo"] == 100.0
        assert scores["overall"] == 83.0
        assert scores["grade"] == "B"

    def test_scoring_falls_back_when_rule_not_found(self):
        """Test fallback to severity weights when rule not in DB."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        violations = [
            {
                "category": "irdai",
                "severity": "critical",
                "description": "Test violation",
                "rule_id": "nonexistent-rule"
            }
        ]

        scores = ScoringService.calculate_scores(violations, db=mock_db)

        # Should fall back to severity-based weight (critical = -20)
        assert scores["irdai"] == 80.0

    def test_multiple_violations_same_category(self):
        """Test scoring with multiple violations in same category."""
        violations = [
            {"category": "irdai", "severity": "critical", "description": "Violation 1"},
            {"category": "irdai", "severity": "high", "description": "Violation 2"},
            {"category": "irdai", "severity": "medium", "description": "Violation 3"},
        ]

        scores = ScoringService.calculate_scores(violations, db=None)

        # IRDAI: 100 - 20 - 10 - 5 = 65
        assert scores["irdai"] == 65.0
        assert scores["status"] == "failed"  # Below 80

    def test_score_cannot_go_below_zero(self):
        """Test that scores are clamped to 0."""
        violations = [
            {"category": "irdai", "severity": "critical", "description": f"Violation {i}"}
            for i in range(10)  # 10 critical violations = -200 points
        ]

        scores = ScoringService.calculate_scores(violations, db=None)

        # Should be clamped to 0
        assert scores["irdai"] == 0.0
        assert scores["status"] == "failed"

    def test_grade_calculation(self):
        """Test letter grade assignment."""
        test_cases = [
            (95.0, "A"),
            (90.0, "A"),
            (85.0, "B"),
            (75.0, "C"),
            (65.0, "D"),
            (55.0, "F"),
        ]

        for score, expected_grade in test_cases:
            # Create violations that result in specific overall score
            # For simplicity, just test the _get_grade method directly
            grade = ScoringService._get_grade(score)
            assert grade == expected_grade, f"Score {score} should be grade {expected_grade}, got {grade}"

    def test_status_determination(self):
        """Test compliance status logic."""
        # Critical violation = failed
        violations_critical = [
            {"category": "irdai", "severity": "critical", "description": "Critical issue"}
        ]
        scores = ScoringService.calculate_scores(violations_critical, db=None)
        assert scores["status"] == "failed"

        # Score < 60 = failed
        violations_many = [
            {"category": "irdai", "severity": "high", "description": f"Issue {i}"}
            for i in range(5)  # 5 high = -50 points, IRDAI score = 50
        ]
        scores = ScoringService.calculate_scores(violations_many, db=None)
        # Overall: 50*0.5 + 100*0.3 + 100*0.2 = 25 + 30 + 20 = 75
        assert scores["status"] == "flagged"

        # Score >= 80 = passed
        violations_minor = [
            {"category": "seo", "severity": "low", "description": "Minor issue"}
        ]
        scores = ScoringService.calculate_scores(violations_minor, db=None)
        # Overall: 100*0.5 + 100*0.3 + 98*0.2 = 50 + 30 + 19.6 = 99.6
        assert scores["status"] == "passed"
