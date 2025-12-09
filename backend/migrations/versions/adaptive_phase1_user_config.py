"""Add user_config table and adaptive compliance fields

Revision ID: adaptive_phase1
Revises: add_content_chunks_20251207
Create Date: 2025-12-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'adaptive_phase1'
down_revision = 'add_content_chunks_20251207'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_configs table
    op.create_table(
        'user_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('brand_name', sa.String(length=200), nullable=True),
        sa.Column('brand_guidelines', sa.Text(), nullable=True),
        sa.Column('analysis_scope', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('preferred_model', sa.String(length=50), server_default='qwen2.5:7b', nullable=True),
        sa.Column('scoring_weights', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('view_preferences', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_configs_user_id', 'user_configs', ['user_id'], unique=False)
    
    # Add auto-generation tracking fields to rules table
    op.add_column('rules', sa.Column('is_auto_generated', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('rules', sa.Column('generated_from_industry', sa.String(length=100), nullable=True))
    op.add_column('rules', sa.Column('generation_source', sa.Text(), nullable=True))
    op.add_column('rules', sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True))
    
    # Create indexes for new columns
    op.create_index('ix_rules_is_auto_generated', 'rules', ['is_auto_generated'], unique=False)
    op.create_index('ix_rules_generated_from_industry', 'rules', ['generated_from_industry'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_rules_generated_from_industry', table_name='rules')
    op.drop_index('ix_rules_is_auto_generated', table_name='rules')
    
    # Drop columns from rules table
    op.drop_column('rules', 'confidence_score')
    op.drop_column('rules', 'generation_source')
    op.drop_column('rules', 'generated_from_industry')
    op.drop_column('rules', 'is_auto_generated')
    
    # Drop user_configs table
    op.drop_index('ix_user_configs_user_id', table_name='user_configs')
    op.drop_table('user_configs')
