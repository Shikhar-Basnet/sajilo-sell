"""fix RLS policies casting empty-string session var to uuid

Revision ID: f1a72d5e8c40
Revises: e5f8a1c2b930
Create Date: 2026-09-29 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a72d5e8c40'
down_revision: Union[str, None] = 'e5f8a1c2b930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app.current_user_id is a custom (placeholder) GUC. current_setting(
    # ..., true) is supposed to return NULL when it was never set — but
    # because connections are pooled and reused across requests, once
    # ANY request on a given physical connection has done a
    # SET LOCAL app.current_user_id = '<uuid>' inside a transaction, that
    # transaction ending resets the value back to '' (empty string), not
    # NULL, for any later request that reuses the same connection without
    # explicitly setting it again. Casting '' directly to uuid then
    # throws invalid_text_representation. nullif(..., '') normalizes the
    # empty-string case back to NULL before the cast, which is what was
    # actually intended.
    op.execute("DROP POLICY IF EXISTS stores_tenant_isolation ON stores;")
    op.execute("""
        CREATE POLICY stores_tenant_isolation ON stores
        USING (
            owner_id = nullif(current_setting('app.current_user_id', true), '')::uuid
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        )
        WITH CHECK (
            owner_id = nullif(current_setting('app.current_user_id', true), '')::uuid
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        );
    """)

    op.execute("DROP POLICY IF EXISTS products_tenant_isolation ON products;")
    op.execute("""
        CREATE POLICY products_tenant_isolation ON products
        USING (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = nullif(current_setting('app.current_user_id', true), '')::uuid
            )
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        )
        WITH CHECK (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = nullif(current_setting('app.current_user_id', true), '')::uuid
            )
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS products_tenant_isolation ON products;")
    op.execute("""
        CREATE POLICY products_tenant_isolation ON products
        USING (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = current_setting('app.current_user_id', true)::uuid
            )
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        )
        WITH CHECK (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = current_setting('app.current_user_id', true)::uuid
            )
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        );
    """)

    op.execute("DROP POLICY IF EXISTS stores_tenant_isolation ON stores;")
    op.execute("""
        CREATE POLICY stores_tenant_isolation ON stores
        USING (
            owner_id = current_setting('app.current_user_id', true)::uuid
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        )
        WITH CHECK (
            owner_id = current_setting('app.current_user_id', true)::uuid
            OR coalesce(current_setting('app.is_admin', true), 'false') = 'true'
        );
    """)