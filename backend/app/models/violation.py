from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from ..database import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_id = Column(UUID(as_uuid=True), ForeignKey("compliance_checks.id", ondelete="CASCADE"))
    rule_id = Column(UUID(as_uuid=True), ForeignKey("rules.id"), nullable=True)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    category = Column(String(20), nullable=False)  # irdai, brand, seo
    description = Column(Text, nullable=False)
    location = Column(String(500))
    current_text = Column(Text)
    suggested_fix = Column(Text)
    is_auto_fixable = Column(Boolean, default=False)

    # Relationships
    check = relationship("ComplianceCheck", back_populates="violations")
    rule = relationship("Rule")
