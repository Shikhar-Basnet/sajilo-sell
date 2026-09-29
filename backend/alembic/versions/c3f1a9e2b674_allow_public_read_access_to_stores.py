"""allow public read access to stores for storefront pages

Revision ID: c3f1a9e2b674
Revises: 98159cfb7048
Create Date: 2026-09-27 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f1a9e2b674'
down_revision: Union[str, None] = '98159cfb7048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Storefront pages must be readable by anyone, including anonymous
    # visitors — there's no app.current_user_id set for those requests.
    # Postgres RLS ORs multiple permissive policies together for the same
    # command, so adding this unconditional SELECT-only policy makes rows
    # readable by everyone while stores_tenant_isolation still governs
    # INSERT/UPDATE/DELETE (owners can only write their own row).
    op.execute("""
        CREATE POLICY stores_public_read ON stores
        FOR SELECT
        USING (true);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS stores_public_read ON stores;")