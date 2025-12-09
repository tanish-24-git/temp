"""Dashboard response schemas for API endpoints."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TrendDataPoint(BaseModel):
    """Single data point in compliance trends."""
    date: datetime
    avg_score: float
    submission_count: int


class ComplianceTrendsResponse(BaseModel):
    """Response for /api/dashboard/trends endpoint."""
    dates: List[str]  # ISO format datetime strings
    scores: List[float]
    counts: List[int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "dates": ["2025-12-01", "2025-12-02", "2025-12-03"],
                "scores": [85.5, 87.2, 89.0],
                "counts": [3, 5, 2]
            }
        }


class HeatmapSeriesItem(BaseModel):
    """Single series in heatmap (severity level)."""
    name: str  # Critical, High, Medium, Low
    data: List[int]  # Counts per category


class ViolationsHeatmapResponse(BaseModel):
    """Response for /api/dashboard/violations-heatmap endpoint.
    
    Returns data in ApexCharts-ready format.
    """
    series: List[HeatmapSeriesItem]
    categories: List[str]  # IRDAI, Brand, SEO
    
    class Config:
        json_schema_extra = {
            "example": {
                "series": [
                    {"name": "Critical", "data": [5, 2, 1]},
                    {"name": "High", "data": [8, 4, 3]},
                    {"name": "Medium", "data": [12, 7, 5]},
                    {"name": "Low", "data": [15, 10, 8]}
                ],
                "categories": ["IRDAI", "Brand", "SEO"]
            }
        }


class TopViolationResponse(BaseModel):
    """Single item in top violations list."""
    description: str
    count: int
    severity: str
    category: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Missing mandatory disclosure statement",
                "count": 15,
                "severity": "critical",
                "category": "irdai"
            }
        }
