"""Add agent observability tables

Revision ID: 7b8c9d0e1f2g
Revises: 6a7b8c9d0e1f
Create Date: 2025-12-07

Creates tables for:
- agent_executions: Track agent runs
- tool_invocations: Track tool usage (premium vs standard)
- agent_metrics: Daily aggregated metrics
- knowledge_base: Regulatory document storage
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '7b8c9d0e1f2g'
down_revision: Union[str, Sequence[str], None] = '6a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agent observability tables."""
    
    # Agent executions - tracks every agent run
    op.create_table('agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='running', nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), server_default='0', nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_executions_agent_type', 'agent_executions', ['agent_type'])
    op.create_index('ix_agent_executions_session_id', 'agent_executions', ['session_id'])
    op.create_index('ix_agent_executions_started_at', 'agent_executions', ['started_at'])
    
    # Tool invocations - tracks every tool call
    op.create_table('tool_invocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('is_premium', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(10, 6), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['agent_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_invocations_tool_name', 'tool_invocations', ['tool_name'])
    op.create_index('ix_tool_invocations_is_premium', 'tool_invocations', ['is_premium'])
    op.create_index('ix_tool_invocations_created_at', 'tool_invocations', ['created_at'])
    
    # Agent metrics - daily aggregated stats
    op.create_table('agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=True),
        sa.Column('total_invocations', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_execution_time_ms', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_cost_usd', sa.Numeric(10, 6), server_default='0', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'agent_type', 'tool_name', name='uq_agent_metrics_date_type_tool')
    )
    op.create_index('ix_agent_metrics_date', 'agent_metrics', ['date'])
    
    # Knowledge base - regulatory documents for RAG
    op.create_table('knowledge_base',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('regulation_name', sa.String(255), nullable=False),
        sa.Column('document_title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_base_country', 'knowledge_base', ['country_code'])
    op.create_index('ix_knowledge_base_regulation', 'knowledge_base', ['regulation_name'])


def downgrade() -> None:
    """Drop agent observability tables."""
    op.drop_table('knowledge_base')
    op.drop_table('agent_metrics')
    op.drop_table('tool_invocations')
    op.drop_table('agent_executions')
