"""add onboarding fields to users table

Revision ID: a1b2c3d4e5f6
Revises: 904afe60c1ce
Create Date: 2026-05-15 23:14:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '904afe60c1ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add onboarding/profile columns to users table."""
    op.add_column('users', sa.Column('gender', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('industry', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('work_start_time', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('work_end_time', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Remove onboarding/profile columns from users table."""
    op.drop_column('users', 'work_end_time')
    op.drop_column('users', 'work_start_time')
    op.drop_column('users', 'industry')
    op.drop_column('users', 'age')
    op.drop_column('users', 'gender')
