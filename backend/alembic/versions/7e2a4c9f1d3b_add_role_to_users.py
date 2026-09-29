"""add role to users

Revision ID: 7e2a4c9f1d3b
Revises: c3f1a9e2b674
Create Date: 2026-09-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e2a4c9f1d3b'
down_revision: Union[str, None] = 'c3f1a9e2b674'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('role', sa.String(length=20), nullable=False, server_default='seller'),
    )
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('seller', 'admin'));"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
    op.drop_column('users', 'role')