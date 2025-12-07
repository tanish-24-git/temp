"""Add Phase 2 fields: points_deduction and created_by to rules table

Revision ID: add_phase2_fields
Revises: 5f282a94fd98
Create Date: 2025-12-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_phase2_fields'
down_revision = '5f282a94fd98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Phase 2 fields for dynamic rule generation and super admin features."""

    # Add points_deduction column to rules table
    # Default -5.00 for medium severity rules
    op.add_column('rules', sa.Column(
        'points_deduction',
        sa.Numeric(precision=5, scale=2),
        nullable=False,
        server_default='-5.00'
    ))

    # Add created_by column to track rule creator (super admin)
    # Nullable initially for backward compatibility with existing rules
    op.add_column('rules', sa.Column(
        'created_by',
        postgresql.UUID(as_uuid=True),
        nullable=True
    ))

    # Create foreign key constraint to users table
    op.create_foreign_key(
        'fk_rules_created_by_users',
        'rules', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'  # If user deleted, keep rule but set creator to NULL
    )

    # Create indexes for better query performance
    op.create_index(
        'ix_rules_created_by',
        'rules',
        ['created_by']
    )

    op.create_index(
        'ix_rules_category',
        'rules',
        ['category']
    )

    op.create_index(
        'ix_rules_severity',
        'rules',
        ['severity']
    )

    # Backfill existing rules with appropriate point deductions based on severity
    # This ensures all existing rules have meaningful point values
    op.execute("""
        UPDATE rules
        SET points_deduction = CASE
            WHEN severity = 'critical' THEN -20.00
            WHEN severity = 'high' THEN -10.00
            WHEN severity = 'medium' THEN -5.00
            WHEN severity = 'low' THEN -2.00
            ELSE -5.00
        END
        WHERE points_deduction = -5.00;
    """)

    # Add comment to explain the new columns
    op.execute("""
        COMMENT ON COLUMN rules.points_deduction IS
        'Point deduction value for compliance score calculation. Negative values indicate penalties.';
    """)

    op.execute("""
        COMMENT ON COLUMN rules.created_by IS
        'UUID of the super admin who created this rule. NULL for system-seeded rules.';
    """)


def downgrade() -> None:
    """Remove Phase 2 fields if rollback is needed."""

    # Drop indexes first
    op.drop_index('ix_rules_severity', table_name='rules')
    op.drop_index('ix_rules_category', table_name='rules')
    op.drop_index('ix_rules_created_by', table_name='rules')

    # Drop foreign key constraint
    op.drop_constraint('fk_rules_created_by_users', 'rules', type_='foreignkey')

    # Drop columns
    op.drop_column('rules', 'created_by')
    op.drop_column('rules', 'points_deduction')
