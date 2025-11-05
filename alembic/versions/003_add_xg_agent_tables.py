"""Add XG Agent tables (retail_analyses, email_analyses, workflow_executions)

Revision ID: 003_add_xg_agent_tables
Revises: 002_add_user_password
Create Date: 2025-01-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '003_add_xg_agent_tables'
down_revision: Union[str, None] = '002_add_user_password'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create retail_analyses table
    op.create_table(
        'retail_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('analysis_results', postgresql.JSONB, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('ix_retail_analyses_organization_id', 'organization_id'),
        sa.Index('ix_retail_analyses_user_id', 'user_id'),
        sa.Index('ix_retail_analyses_created_at', 'created_at'),
    )
    
    # Create email_analyses table
    op.create_table(
        'email_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('emails_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('analysis_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('drafts_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('email_summary', sa.Text, nullable=True),
        sa.Column('email_analysis_results', postgresql.JSONB, nullable=True),
        sa.Column('email_visualizations', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('ix_email_analyses_organization_id', 'organization_id'),
        sa.Index('ix_email_analyses_user_id', 'user_id'),
        sa.Index('ix_email_analyses_created_at', 'created_at'),
    )
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', sa.String(255), nullable=False, unique=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mode', sa.String(50), nullable=False),  # 'retail', 'email', 'meeting'
        sa.Column('status', sa.String(50), nullable=False),  # 'pending', 'running', 'completed', 'failed'
        sa.Column('result', postgresql.JSONB, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.Index('ix_workflow_executions_workflow_id', 'workflow_id'),
        sa.Index('ix_workflow_executions_organization_id', 'organization_id'),
        sa.Index('ix_workflow_executions_user_id', 'user_id'),
        sa.Index('ix_workflow_executions_meeting_id', 'meeting_id'),
        sa.Index('ix_workflow_executions_mode', 'mode'),
        sa.Index('ix_workflow_executions_status', 'status'),
        sa.Index('ix_workflow_executions_created_at', 'created_at'),
    )


def downgrade() -> None:
    op.drop_table('workflow_executions')
    op.drop_table('email_analyses')
    op.drop_table('retail_analyses')



