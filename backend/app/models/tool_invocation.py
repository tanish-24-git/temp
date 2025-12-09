"""ToolInvocation SQLAlchemy Model"""

from sqlalchemy import Column, String, Integer, Boolean, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class ToolInvocation(Base):
    """Tracks every tool invocation with premium/billing tracking."""
    __tablename__ = "tool_invocations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    execution_id = Column(UUID(as_uuid=True), 
                          ForeignKey('agent_executions.id', ondelete='CASCADE'),
                          nullable=False)
    tool_name = Column(String(100), nullable=False, index=True)
    is_premium = Column(Boolean, default=False, index=True)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    execution = relationship("AgentExecution", back_populates="tool_invocations")
    
    def __repr__(self):
        premium = " [PREMIUM]" if self.is_premium else ""
        return f"<ToolInvocation {self.tool_name}{premium}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "execution_id": str(self.execution_id),
            "tool_name": self.tool_name,
            "is_premium": self.is_premium,
            "tokens_used": self.tokens_used,
            "execution_time_ms": self.execution_time_ms,
            "cost_usd": float(self.cost_usd) if self.cost_usd else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
