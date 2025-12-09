"""AgentExecution SQLAlchemy Model"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class AgentExecution(Base):
    """Tracks every agent execution for observability."""
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    agent_type = Column(String(50), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'),
                     nullable=True)
    status = Column(String(20), default='running')
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    tool_invocations = relationship("ToolInvocation", back_populates="execution",
                                     cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentExecution {self.agent_type} session={self.session_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "session_id": str(self.session_id),
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tokens_used": self.total_tokens_used,
            "execution_time_ms": self.execution_time_ms
        }
