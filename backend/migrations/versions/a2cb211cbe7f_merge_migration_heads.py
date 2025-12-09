"""Merge migration heads

Revision ID: a2cb211cbe7f
Revises: 2bca567a0c68, adaptive_phase1
Create Date: 2025-12-08 08:42:43.882529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2cb211cbe7f'
down_revision: Union[str, Sequence[str], None] = ('2bca567a0c68', 'adaptive_phase1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
