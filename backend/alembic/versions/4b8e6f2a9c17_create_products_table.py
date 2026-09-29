"""create products table and enable RLS

Revision ID: 4b8e6f2a9c17
Revises: 7e2a4c9f1d3b
Create Date: 2026-09-29 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4b8e6f2a9c17'
down_revision: Union[str, None] = '7e2a4c9f1d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('store_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_store_id'), 'products', ['store_id'], unique=False)

    # sajilo_app already has SELECT/INSERT/UPDATE/DELETE on this table via
    # the ALTER DEFAULT PRIVILEGES set up in 98159cfb7048 — no extra GRANT
    # needed here, as long as this migration runs via the same admin
    # DATABASE_URL role that owns the existing tables.

    op.execute("ALTER TABLE products ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE products FORCE ROW LEVEL SECURITY;")

    # Owner can read/write only products belonging to their own store.
    # Ownership is one hop away (via store_id -> stores.owner_id), unlike
    # stores' own policy which checks owner_id directly on the row.
    op.execute("""
        CREATE POLICY products_tenant_isolation ON products
        USING (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = current_setting('app.current_user_id', true)::uuid
            )
        )
        WITH CHECK (
            store_id IN (
                SELECT id FROM stores
                WHERE owner_id = current_setting('app.current_user_id', true)::uuid
            )
        );
    """)

    # Anonymous storefront visitors can read active products from any
    # store. Inactive products stay invisible to everyone except the
    # owning tenant (covered by products_tenant_isolation above).
    op.execute("""
        CREATE POLICY products_public_read ON products
        FOR SELECT
        USING (is_active = true);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS products_public_read ON products;")
    op.execute("DROP POLICY IF EXISTS products_tenant_isolation ON products;")
    op.execute("ALTER TABLE products NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE products DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f('ix_products_store_id'), table_name='products')
    op.drop_table('products')