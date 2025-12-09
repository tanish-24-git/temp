"""
DeepAnalysis SQLAlchemy Model

Stores the complete deep analysis result for a submission as a single JSON document.
This approach simplifies storage and retrieval while maintaining full audit trail.
"""

from sqlalchemy import Column, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class DeepAnalysis(Base):
    """
    Stores complete deep analysis for a submission as a single document.
    
    Instead of storing one row per line, we store the entire analysis
    as a JSON array in the 'analysis_data' field.
    
    Governance Features:
    - severity_config_snapshot: Stores exact weights used (audit trail)
    - analysis_data: Complete line-by-line results with rule impacts
    - summary stats stored for quick retrieval
    """
    __tablename__ = "deep_analysis"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    
    # Foreign key to compliance_checks
    check_id = Column(UUID(as_uuid=True), 
                      ForeignKey('compliance_checks.id', ondelete='CASCADE'),
                      nullable=False, index=True, unique=True)  # One analysis per check
    
    # Summary stats for quick display
    total_lines = Column(Numeric(10, 0), default=0)
    average_score = Column(Numeric(5, 2), default=100.0)
    min_score = Column(Numeric(5, 2), default=100.0)
    max_score = Column(Numeric(5, 2), default=100.0)
    
    # Document title for display
    document_title = Column(Text, nullable=True)
    
    # Governance snapshot: exact weights used for this analysis run
    # Format: {"critical": 1.5, "high": 1.0, "medium": 0.5, "low": 0.2}
    severity_config_snapshot = Column(JSONB, nullable=False)

    # Analysis Status: pending, processing, completed, failed
    status = Column(Text, default='pending', server_default='pending')

    
    # Complete analysis data as JSON array
    # Format: [{
    #   "line_number": 1,
    #   "line_content": "...",
    #   "line_score": 85.0,
    #   "relevance_context": "...",
    #   "rule_impacts": [{"rule_id": "...", "severity": "...", ...}]
    # }]
    analysis_data = Column(JSONB, default=[], server_default='[]')
    
    # Timestamp for audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to compliance check
    compliance_check = relationship("ComplianceCheck", backref="deep_analysis")
    
    def __repr__(self):
        return f"<DeepAnalysis check_id={self.check_id} lines={self.total_lines} avg={self.average_score}>"
    
    def to_response_dict(self, submission_id: str) -> dict:
        """Convert to API response format."""
        return {
            "check_id": str(self.check_id),
            "submission_id": submission_id,
            "document_title": self.document_title or "",
            "total_lines": int(self.total_lines) if self.total_lines else 0,
            "average_score": float(self.average_score) if self.average_score else 100.0,
            "average_score": float(self.average_score) if self.average_score else 100.0,
            "min_score": float(self.min_score) if self.min_score else 100.0,
            "max_score": float(self.max_score) if self.max_score else 100.0,
            "severity_config": self.severity_config_snapshot or {},
            "status": self.status or "completed",
            "lines": self.analysis_data or [],
            "analysis_timestamp": self.created_at.isoformat() if self.created_at else None
        }
