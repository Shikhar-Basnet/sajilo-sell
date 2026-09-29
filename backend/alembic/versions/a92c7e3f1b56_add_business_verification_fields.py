"""add business verification fields and rejection reason to stores

Revision ID: a92c7e3f1b56
Revises: f1a72d5e8c40
Create Date: 2026-09-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a92c7e3f1b56'
down_revision: Union[str, None] = 'f1a72d5e8c40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable at the DB level even though required by the Pydantic
    # schema for new registrations — avoids needing to backfill values
    # for stores created before this migration.
    op.add_column('stores', sa.Column('legal_business_name', sa.String(length=255), nullable=True))
    op.add_column('stores', sa.Column('owner_full_name', sa.String(length=255), nullable=True))
    op.add_column('stores', sa.Column('pan_number', sa.String(length=50), nullable=True))
    op.add_column('stores', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('stores', 'rejection_reason')
    op.drop_column('stores', 'pan_number')
    op.drop_column('stores', 'owner_full_name')
    op.drop_column('stores', 'legal_business_name')