"""UserConfig SQLAlchemy Model

Stores user preferences, onboarding data, and configuration.
Enables personalized compliance analysis based on industry and scope.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class UserConfig(Base):
    """
    User configuration and preferences.
    
    Stores:
    - Onboarding data (industry, brand, scope)
    - Model preferences
    - Scoring weights customization
    - UI view preferences
    
    Enables adaptive compliance analysis tailored to user context.
    """
    __tablename__ = "user_configs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=func.gen_random_uuid())
    
    # Foreign key to users
    user_id = Column(UUID(as_uuid=True), 
                    ForeignKey('users.id', ondelete='CASCADE'),
                    nullable=False, unique=True, index=True)
    
    # === Onboarding Data ===
    industry = Column(String(100), nullable=True)
    # Examples: "insurance", "healthcare", "finance", "ecommerce"
    
    brand_name = Column(String(200), nullable=True)
    # Company/brand name for personalization
    
    brand_guidelines = Column(Text, nullable=True)
    # Optional: User-uploaded brand guidelines text
    
    analysis_scope = Column(ARRAY(String), default=list, server_default='{}')
    # Selected analysis categories: ["regulatory", "brand", "seo", "qualitative"]
    
    # === Model Preferences (Phase 2) ===
    preferred_model = Column(String(50), default="qwen2.5:7b")
    # LLM model selection for analysis
    
    # === Scoring Weights (Phase 2) ===
    scoring_weights = Column(JSONB, default={}, server_default='{}')
    # Custom category weights: {"irdai": 0.6, "brand": 0.3, "seo": 0.1}
    
    # === View Preferences (Phase 2) ===
    view_preferences = Column(JSONB, default={}, server_default='{}')
    # UI toggles: {"show_chunk_stats": true, "show_relevance": false}
    
    # === Metadata ===
    onboarding_completed = Column(Boolean, default=False)
    # Track if user completed initial onboarding
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="config")
    
    def __repr__(self):
        return f"<UserConfig user_id={self.user_id} industry={self.industry}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "industry": self.industry,
            "brand_name": self.brand_name,
            "brand_guidelines": self.brand_guidelines,
            "analysis_scope": self.analysis_scope or [],
            "preferred_model": self.preferred_model,
            "scoring_weights": self.scoring_weights or {},
            "view_preferences": self.view_preferences or {},
            "onboarding_completed": self.onboarding_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_effective_weights(self) -> dict:
        """
        Get scoring weights with fallback to defaults.
        
        Returns standard weights if user hasn't customized.
        """
        if self.scoring_weights:
            return self.scoring_weights
        
        # Default weights
        return {
            "irdai": 0.50,
            "brand": 0.30,
            "seo": 0.20
        }
    
    def is_scope_enabled(self, category: str) -> bool:
        """Check if a category is in user's selected scope."""
        if not self.analysis_scope:
            # Default: all categories enabled
            return True
        return category in self.analysis_scope
