"""Add dashboard performance indexes

Revision ID: 8c9d0e1f2g3h
Revises: 7b8c9d0e1f2g
Create Date: 2025-12-07

Creates indexes for dashboard queries:
- compliance_checks.check_date for trend queries
- violations.category/severity for heatmap queries
- Composite indexes for efficient aggregations
"""
from typing import Sequence, Union

from alembic import op


revision: str = '8c9d0e1f2g3h'
down_revision: Union[str, Sequence[str], None] = '7b8c9d0e1f2g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create indexes for dashboard queries."""
    
    # Index for compliance trends (ORDER BY check_date DESC)
    op.create_index(
        'ix_compliance_checks_check_date', 
        'compliance_checks', 
        ['check_date'],
        postgresql_using='btree'
    )
    
    # Indexes for violation analysis
    op.create_index(
        'ix_violations_category', 
        'violations', 
        ['category'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'ix_violations_severity', 
        'violations', 
        ['severity'],
        postgresql_using='btree'
    )
    
    # Composite index for heatmap query (category + severity)
    op.create_index(
        'ix_violations_category_severity', 
        'violations', 
        ['category', 'severity'],
        postgresql_using='btree'
    )
    
    # Composite index for joins (check_id + category/severity)
    op.create_index(
        'ix_violations_check_id_category', 
        'violations', 
        ['check_id', 'category'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Drop dashboard indexes."""
    op.drop_index('ix_violations_check_id_category', 'violations')
    op.drop_index('ix_violations_category_severity', 'violations')
    op.drop_index('ix_violations_severity', 'violations')
    op.drop_index('ix_violations_category', 'violations')
    op.drop_index('ix_compliance_checks_check_date', 'compliance_checks')
