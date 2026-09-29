"""add customer role and store approval workflow

Revision ID: e5f8a1c2b930
Revises: 4b8e6f2a9c17
Create Date: 2026-09-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f8a1c2b930'
down_revision: Union[str, None] = '4b8e6f2a9c17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'seller', 'customer'));")
    op.alter_column('users', 'role', server_default='customer')

    op.add_column('stores', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('stores', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    op.add_column('stores', sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'))
    op.execute("ALTER TABLE stores ADD CONSTRAINT stores_status_check CHECK (status IN ('pending', 'approved', 'rejected'));")

    # Grandfather in stores created before this workflow existed, so they
    # don't silently disappear from the public storefront the moment
    # stores_public_read starts filtering on status.
    op.execute("UPDATE stores SET status = 'approved' WHERE status = 'pending';")

    # Rebuild stores RLS: owners keep full access to their own row
    # regardless of status; admins (flagged via app.is_admin, set by
    # get_admin_db) bypass tenant scoping entirely; the public can only
    # SELECT approved stores.
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
    op.execute("DROP POLICY IF EXISTS stores_public_read ON stores;")
    op.execute("""
        CREATE POLICY stores_public_read ON stores
        FOR SELECT
        USING (status = 'approved');
    """)

    # Rebuild products RLS to match: owners (via their store) and admins
    # get full access; the public only sees active products belonging to
    # an approved store.
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
    op.execute("DROP POLICY IF EXISTS products_public_read ON products;")
    op.execute("""
        CREATE POLICY products_public_read ON products
        FOR SELECT
        USING (
            is_active = true
            AND store_id IN (SELECT id FROM stores WHERE status = 'approved')
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS products_public_read ON products;")
    op.execute("CREATE POLICY products_public_read ON products FOR SELECT USING (is_active = true);")
    op.execute("DROP POLICY IF EXISTS products_tenant_isolation ON products;")
    op.execute("""
        CREATE POLICY products_tenant_isolation ON products
        USING (store_id IN (SELECT id FROM stores WHERE owner_id = current_setting('app.current_user_id', true)::uuid))
        WITH CHECK (store_id IN (SELECT id FROM stores WHERE owner_id = current_setting('app.current_user_id', true)::uuid));
    """)

    op.execute("DROP POLICY IF EXISTS stores_public_read ON stores;")
    op.execute("CREATE POLICY stores_public_read ON stores FOR SELECT USING (true);")
    op.execute("DROP POLICY IF EXISTS stores_tenant_isolation ON stores;")
    op.execute("""
        CREATE POLICY stores_tenant_isolation ON stores
        USING (owner_id = current_setting('app.current_user_id', true)::uuid)
        WITH CHECK (owner_id = current_setting('app.current_user_id', true)::uuid);
    """)

    op.execute("ALTER TABLE stores DROP CONSTRAINT IF EXISTS stores_status_check;")
    op.drop_column('stores', 'status')
    op.drop_column('stores', 'contact_phone')
    op.drop_column('stores', 'description')

    op.alter_column('users', 'role', server_default='seller')
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('seller', 'admin'));")