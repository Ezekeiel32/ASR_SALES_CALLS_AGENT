"""Add password_hash to users table

Revision ID: 002_add_user_password
Revises: 001_initial_schema
Create Date: 2025-01-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_user_password'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to users table
    op.add_column(
        'users',
        sa.Column('password_hash', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'password_hash')

