"""merge migration heads

Revision ID: 6618fd92fa5c
Revises: b7d3c1e9f204, d4f8b2a91c33
Create Date: 2026-09-30 18:12:05.477914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6618fd92fa5c'
down_revision: Union[str, None] = ('b7d3c1e9f204', 'd4f8b2a91c33')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass


