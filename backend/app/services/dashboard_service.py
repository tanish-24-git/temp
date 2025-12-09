"""Dashboard analytics service for aggregated compliance data."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, cast, Date
from sqlalchemy.dialects.postgresql import aggregate_order_by
import logging

from ..models.compliance_check import ComplianceCheck
from ..models.violation import Violation
from ..schemas.dashboard import (
    ComplianceTrendsResponse,
    ViolationsHeatmapResponse,
    HeatmapSeriesItem,
    TopViolationResponse
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregations and analytics.
    
    Provides efficient queries for:
    - Compliance score trends over time
    - Violation distribution heatmap
    - Top occurring violations
    """
    
    # Category display names
    CATEGORIES = ["irdai", "brand", "seo"]
    CATEGORY_DISPLAY = {"irdai": "IRDAI", "brand": "Brand", "seo": "SEO"}
    
    # Severity levels in order
    SEVERITIES = ["critical", "high", "medium", "low"]
    SEVERITY_DISPLAY = {
        "critical": "Critical",
        "high": "High", 
        "medium": "Medium",
        "low": "Low"
    }

    def get_compliance_trends(
        self, 
        db: Session, 
        days: int = 30
    ) -> ComplianceTrendsResponse:
        """Get daily compliance score trends using date bucketing.
        
        Args:
            db: Database session
            days: Number of days to look back (default 30)
            
        Returns:
            ComplianceTrendsResponse with dates, scores, and counts arrays
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query daily aggregates
            daily_stats = db.query(
                cast(ComplianceCheck.check_date, Date).label('date'),
                func.avg(ComplianceCheck.overall_score).label('avg_score'),
                func.count(ComplianceCheck.id).label('count')
            ).filter(
                ComplianceCheck.check_date >= start_date,
                ComplianceCheck.check_date <= end_date
            ).group_by(
                cast(ComplianceCheck.check_date, Date)
            ).order_by(
                cast(ComplianceCheck.check_date, Date)
            ).all()
            
            # If no data, return empty but valid response
            if not daily_stats:
                logger.info("No compliance data found for trends")
                return ComplianceTrendsResponse(
                    dates=[],
                    scores=[],
                    counts=[]
                )
            
            # Build response arrays
            dates = []
            scores = []
            counts = []
            
            for stat in daily_stats:
                dates.append(stat.date.isoformat())
                scores.append(round(float(stat.avg_score or 0), 2))
                counts.append(stat.count)
            
            logger.info(f"Retrieved {len(dates)} days of trend data")
            
            return ComplianceTrendsResponse(
                dates=dates,
                scores=scores,
                counts=counts
            )
            
        except Exception as e:
            logger.error(f"Error fetching compliance trends: {str(e)}")
            # Return empty response on error
            return ComplianceTrendsResponse(
                dates=[],
                scores=[],
                counts=[]
            )

    def get_violations_heatmap(self, db: Session) -> ViolationsHeatmapResponse:
        """Get violation distribution pivoted by category and severity.
        
        Returns data in ApexCharts-ready format with series and categories.
        Uses CASE statements to pivot data in a single query.
        
        Args:
            db: Database session
            
        Returns:
            ViolationsHeatmapResponse with series (severity levels) and categories
        """
        try:
            # Pivot query using CASE statements
            # Count violations per category for each severity level
            heatmap_data = db.query(
                Violation.severity,
                func.sum(case((Violation.category == 'irdai', 1), else_=0)).label('irdai_count'),
                func.sum(case((Violation.category == 'brand', 1), else_=0)).label('brand_count'),
                func.sum(case((Violation.category == 'seo', 1), else_=0)).label('seo_count')
            ).group_by(
                Violation.severity
            ).all()
            
            # Build severity -> counts mapping
            severity_counts = {
                'critical': [0, 0, 0],
                'high': [0, 0, 0],
                'medium': [0, 0, 0],
                'low': [0, 0, 0]
            }
            
            for row in heatmap_data:
                if row.severity in severity_counts:
                    severity_counts[row.severity] = [
                        int(row.irdai_count or 0),
                        int(row.brand_count or 0),
                        int(row.seo_count or 0)
                    ]
            
            # Build series in order (Critical, High, Medium, Low)
            series = [
                HeatmapSeriesItem(
                    name=self.SEVERITY_DISPLAY[sev],
                    data=severity_counts[sev]
                )
                for sev in self.SEVERITIES
            ]
            
            # Categories for x-axis
            categories = [self.CATEGORY_DISPLAY[cat] for cat in self.CATEGORIES]
            
            logger.info(f"Retrieved heatmap data: {sum(sum(s.data) for s in series)} total violations")
            
            return ViolationsHeatmapResponse(
                series=series,
                categories=categories
            )
            
        except Exception as e:
            logger.error(f"Error fetching violations heatmap: {str(e)}")
            # Return zeroed structure on error
            return ViolationsHeatmapResponse(
                series=[
                    HeatmapSeriesItem(name="Critical", data=[0, 0, 0]),
                    HeatmapSeriesItem(name="High", data=[0, 0, 0]),
                    HeatmapSeriesItem(name="Medium", data=[0, 0, 0]),
                    HeatmapSeriesItem(name="Low", data=[0, 0, 0])
                ],
                categories=["IRDAI", "Brand", "SEO"]
            )

    def get_top_violations(
        self, 
        db: Session, 
        limit: int = 5
    ) -> List[TopViolationResponse]:
        """Get most frequently occurring violations.
        
        Groups by violation description, counts occurrences,
        and returns the top N violations.
        
        Args:
            db: Database session
            limit: Maximum number of violations to return (default 5)
            
        Returns:
            List of TopViolationResponse items
        """
        try:
            # Group by description and count occurrences
            top_violations = db.query(
                Violation.description,
                Violation.category,
                Violation.severity,
                func.count(Violation.id).label('count')
            ).group_by(
                Violation.description,
                Violation.category,
                Violation.severity
            ).order_by(
                desc('count')
            ).limit(limit).all()
            
            if not top_violations:
                logger.info("No violations found for top violations query")
                return []
            
            result = [
                TopViolationResponse(
                    description=v.description,
                    count=v.count,
                    severity=v.severity,
                    category=v.category
                )
                for v in top_violations
            ]
            
            logger.info(f"Retrieved top {len(result)} violations")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching top violations: {str(e)}")
            return []


# Singleton instance
dashboard_service = DashboardService()
