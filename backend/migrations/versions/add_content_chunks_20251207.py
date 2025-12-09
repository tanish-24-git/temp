"""add content chunks table

Revision ID: add_content_chunks_20251207
Revises: add_phase2_fields
Create Date: 2025-12-07 15:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_content_chunks_20251207'
down_revision = 'add_phase2_fields'  # Fixed to match actual revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create content_chunks table for granular content processing.
    Update submissions.status to support new preprocessing states.
    """
    # Create content_chunks table
    op.create_table(
        'content_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                 server_default=sa.text('gen_random_uuid()'),
                 primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), server_default='0'),
        sa.Column('chunk_metadata', postgresql.JSONB(), server_default='{}'),  # Renamed from 'metadata'
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_content_chunks_submission_id', 'content_chunks', ['submission_id'])
    op.create_index('ix_content_chunks_chunk_index', 'content_chunks', ['chunk_index'])
    op.create_index('ix_content_chunks_submission_chunk', 'content_chunks', 
                   ['submission_id', 'chunk_index'], unique=True)
    
    # Update existing submissions status values
    # Old: pending, analyzing, completed, failed
    # New: uploaded, preprocessing, preprocessed, analyzing, analyzed, failed
    op.execute("""
        UPDATE submissions 
        SET status = CASE 
            WHEN status = 'pending' THEN 'uploaded'
            WHEN status = 'analyzing' THEN 'analyzing'
            WHEN status = 'completed' THEN 'analyzed'
            WHEN status = 'failed' THEN 'failed'
            ELSE status
        END
    """)


def downgrade() -> None:
    """
    Drop content_chunks table and revert submission status values.
    """
    # Drop indexes
    op.drop_index('ix_content_chunks_submission_chunk', table_name='content_chunks')
    op.drop_index('ix_content_chunks_chunk_index', table_name='content_chunks')
    op.drop_index('ix_content_chunks_submission_id', table_name='content_chunks')
    
    # Drop table
    op.drop_table('content_chunks')
    
    # Revert status values
    op.execute("""
        UPDATE submissions 
        SET status = CASE 
            WHEN status IN ('uploaded', 'preprocessing', 'preprocessed') THEN 'pending'
            WHEN status = 'analyzing' THEN 'analyzing'
            WHEN status = 'analyzed' THEN 'completed'
            WHEN status = 'failed' THEN 'failed'
            ELSE status
        END
    """)
