"""Add deep_analysis table for storing analysis as single JSON

Revision ID: 6a7b8c9d0e1f
Revises: add_phase2_fields
Create Date: 2025-12-07

This table stores the complete deep analysis result for a submission
as a single JSON document, with summary stats for quick retrieval.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6a7b8c9d0e1f'
down_revision: Union[str, Sequence[str], None] = 'add_phase2_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create deep_analysis table with new single-JSON schema."""
    
    # Drop existing table if it exists (from previous migration)
    op.execute("DROP TABLE IF EXISTS deep_analysis CASCADE")
    
    # Create with new schema
    op.create_table('deep_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), 
                  nullable=False),
        sa.Column('check_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Summary stats
        sa.Column('total_lines', sa.Numeric(precision=10, scale=0), 
                  server_default='0', nullable=True),
        sa.Column('average_score', sa.Numeric(precision=5, scale=2), 
                  server_default='100.00', nullable=True),
        sa.Column('min_score', sa.Numeric(precision=5, scale=2), 
                  server_default='100.00', nullable=True),
        sa.Column('max_score', sa.Numeric(precision=5, scale=2), 
                  server_default='100.00', nullable=True),
        
        # Document info
        sa.Column('document_title', sa.Text(), nullable=True),
        
        # Governance snapshot
        sa.Column('severity_config_snapshot', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False),
        
        # Complete analysis as single JSON array
        sa.Column('analysis_data', postgresql.JSONB(astext_type=sa.Text()), 
                  server_default='[]', nullable=True),
        
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        
        # Keys
        sa.ForeignKeyConstraint(['check_id'], ['compliance_checks.id'], 
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('check_id')  # One analysis per check
    )
    
    # Create index for fast lookup
    op.create_index('ix_deep_analysis_check_id', 'deep_analysis', ['check_id'])
    
    # Add table comment
    op.execute("""
        COMMENT ON TABLE deep_analysis IS 
        'Stores complete deep analysis for a submission as a single JSON document';
    """)


def downgrade() -> None:
    """Drop deep_analysis table."""
    op.drop_index('ix_deep_analysis_check_id', table_name='deep_analysis')
    op.drop_table('deep_analysis')
