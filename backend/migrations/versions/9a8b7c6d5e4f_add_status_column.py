"""Add status column to deep_analysis

Revision ID: 9a8b7c6d5e4f
Revises: 6a7b8c9d0e1f
Create Date: 2025-12-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, Sequence[str], None] = '8c9d0e1f2g3h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('deep_analysis', sa.Column('status', sa.Text(), server_default='pending', nullable=True))


def downgrade() -> None:
    op.drop_column('deep_analysis', 'status')
