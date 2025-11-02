"""Initial schema with pgvector support

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subscription_plan', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('sso_provider', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'], unique=False)
    
    # Create speakers table with pgvector
    op.create_table(
        'speakers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('voiceprint_embedding', Vector(256), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='idx_speakers_org_name_unique')
    )
    op.create_index('idx_speakers_organization_id', 'speakers', ['organization_id'], unique=False)
    # Create IVFFlat index for vector similarity search (requires data, so we'll create it separately)
    
    # Create meetings table
    op.create_table(
        'meetings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('audio_s3_key', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('duration_seconds', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_meetings_organization_id', 'meetings', ['organization_id'], unique=False)
    op.create_index('idx_meetings_status', 'meetings', ['status'], unique=False)
    op.create_index('idx_meetings_created_at', 'meetings', ['created_at'], unique=False)
    
    # Create transcription_segments table
    op.create_table(
        'transcription_segments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('meeting_id', sa.UUID(), nullable=False),
        sa.Column('speaker_id', sa.UUID(), nullable=True),
        sa.Column('unidentified_speaker_label', sa.String(length=50), nullable=True),
        sa.Column('start_time_seconds', sa.Float(), nullable=False),
        sa.Column('end_time_seconds', sa.Float(), nullable=False),
        sa.Column('hebrew_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['speaker_id'], ['speakers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_segments_meeting_id', 'transcription_segments', ['meeting_id'], unique=False)
    op.create_index('idx_segments_speaker_id', 'transcription_segments', ['speaker_id'], unique=False)
    op.create_index('idx_segments_start_time', 'transcription_segments', ['start_time_seconds'], unique=False)
    
    # Create meeting_summaries table
    op.create_table(
        'meeting_summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('meeting_id', sa.UUID(), nullable=False),
        sa.Column('summary_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('meeting_id')
    )
    op.create_index('idx_summaries_meeting_id', 'meeting_summaries', ['meeting_id'], unique=False)
    
    # Create name_suggestions table
    op.create_table(
        'name_suggestions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('meeting_id', sa.UUID(), nullable=False),
        sa.Column('unidentified_speaker_label', sa.String(length=50), nullable=False),
        sa.Column('suggested_name', sa.String(length=255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('segment_start_time', sa.Float(), nullable=True),
        sa.Column('segment_end_time', sa.Float(), nullable=True),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_name_suggestions_meeting_id', 'name_suggestions', ['meeting_id'], unique=False)
    op.create_index('idx_name_suggestions_speaker_label', 'name_suggestions', ['unidentified_speaker_label'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_organization_id', 'audit_logs', ['organization_id'], unique=False)
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_organization_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_name_suggestions_speaker_label', table_name='name_suggestions')
    op.drop_index('idx_name_suggestions_meeting_id', table_name='name_suggestions')
    op.drop_table('name_suggestions')
    
    op.drop_index('idx_summaries_meeting_id', table_name='meeting_summaries')
    op.drop_table('meeting_summaries')
    
    op.drop_index('idx_segments_start_time', table_name='transcription_segments')
    op.drop_index('idx_segments_speaker_id', table_name='transcription_segments')
    op.drop_index('idx_segments_meeting_id', table_name='transcription_segments')
    op.drop_table('transcription_segments')
    
    op.drop_index('idx_meetings_created_at', table_name='meetings')
    op.drop_index('idx_meetings_status', table_name='meetings')
    op.drop_index('idx_meetings_organization_id', table_name='meetings')
    op.drop_table('meetings')
    
    op.drop_index('idx_speakers_organization_id', table_name='speakers')
    op.drop_table('speakers')
    
    op.drop_index('idx_users_organization_id', table_name='users')
    op.drop_table('users')
    
    op.drop_table('organizations')
    
    # Note: We don't drop the vector extension as it may be used by other databases

