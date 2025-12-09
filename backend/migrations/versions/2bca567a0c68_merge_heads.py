"""merge_heads

Revision ID: 2bca567a0c68
Revises: 9a8b7c6d5e4f, add_content_chunks_20251207
Create Date: 2025-12-07 09:51:04.260942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bca567a0c68'
down_revision: Union[str, Sequence[str], None] = ('9a8b7c6d5e4f', 'add_content_chunks_20251207')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
