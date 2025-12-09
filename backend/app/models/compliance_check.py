from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"))
    check_date = Column(DateTime(timezone=True), server_default=func.now())
    overall_score = Column(Numeric(5, 2))
    irdai_score = Column(Numeric(5, 2))
    brand_score = Column(Numeric(5, 2))
    seo_score = Column(Numeric(5, 2))
    status = Column(String(50))  # passed, flagged, failed
    ai_summary = Column(Text)
    grade = Column(String(2))

    # Relationships
    submission = relationship("Submission", back_populates="compliance_checks")
    violations = relationship("Violation", back_populates="check", cascade="all, delete-orphan")

    @property
    def has_deep_analysis(self) -> bool:
        """Check if deep analysis results exist for this check."""
        return bool(self.deep_analysis)
