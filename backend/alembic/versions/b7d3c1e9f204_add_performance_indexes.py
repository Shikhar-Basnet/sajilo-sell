# backend/alembic/versions/b7d3c1e9f204_add_performance_indexes.py
"""add performance indexes

Revision ID: b7d3c1e9f204
Revises: a92c7e3f1b56
Create Date: 2026-09-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b7d3c1e9f204'
down_revision: Union[str, None] = 'a92c7e3f1b56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Public storefront product listing: WHERE store_id=? AND is_active ORDER BY created_at DESC
    op.create_index(
        "ix_products_store_active_created", "products",
        ["store_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("is_active"),
    )
    # Public store directory: WHERE status='approved' ORDER BY created_at DESC
    op.create_index(
        "ix_stores_approved_created", "stores",
        [sa.text("created_at DESC")],
        postgresql_where=sa.text("status = 'approved'"),
    )
    # Admin audit log: ORDER BY created_at DESC LIMIT n
    op.create_index("ix_audit_logs_created_at", "audit_logs", [sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_stores_approved_created", table_name="stores")
    op.drop_index("ix_products_store_active_created", table_name="products")