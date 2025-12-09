from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="agent")  # agent, reviewer, super_admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Phase 2: Relationship to rules created by this user (if super_admin)
    created_rules = relationship("Rule", back_populates="creator", foreign_keys="Rule.created_by")
    
    # Adaptive Compliance Engine: User configuration
    config = relationship("UserConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
