from sqlalchemy import Column, String, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(20), nullable=False, index=True)  # irdai, brand, seo
    rule_text = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    keywords = Column(JSONB)  # Array of keywords
    pattern = Column(String(1000))  # Optional regex
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Phase 2: Dynamic rule generation fields
    points_deduction = Column(
        Numeric(5, 2),
        nullable=False,
        default=-5.00,
        comment="Point deduction value for compliance score calculation"
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Super admin who created this rule"
    )

    # Adaptive Compliance Engine: Auto-generation tracking
    is_auto_generated = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True if rule was auto-generated from onboarding"
    )
    generated_from_industry = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Industry context for auto-generated rules (e.g., 'insurance', 'healthcare')"
    )
    generation_source = Column(
        Text,
        nullable=True,
        comment="Source URL or search query used to generate this rule"
    )
    confidence_score = Column(
        Numeric(3, 2),
        nullable=True,
        comment="AI confidence in rule extraction (0.0-1.0)"
    )

    # Relationships
    creator = relationship("User", back_populates="created_rules", foreign_keys=[created_by])
