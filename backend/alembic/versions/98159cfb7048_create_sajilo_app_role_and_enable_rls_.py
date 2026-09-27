"""create sajilo_app role and enable RLS on stores

Revision ID: 98159cfb7048
Revises: 39dd6d42b5ff
Create Date: 2026-09-27 15:51:56.319293

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98159cfb7048'
down_revision: Union[str, None] = '39dd6d42b5ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    app_db_user = os.environ.get("APP_DB_USER", "sajilo_app")
    app_db_password = os.environ["APP_DB_PASSWORD"].replace("'", "''")

    op.execute(f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{app_db_user}') THEN
            CREATE ROLE {app_db_user} LOGIN PASSWORD '{app_db_password}'
              NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
          ELSE
            ALTER ROLE {app_db_user} WITH LOGIN PASSWORD '{app_db_password}'
              NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
          END IF;
        END
        $$;
    """)

    op.execute(f"GRANT USAGE ON SCHEMA public TO {app_db_user};")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {app_db_user};")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {app_db_user};"
    )

    op.execute("ALTER TABLE stores ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE stores FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY stores_tenant_isolation ON stores
        USING (owner_id = current_setting('app.current_user_id', true)::uuid)
        WITH CHECK (owner_id = current_setting('app.current_user_id', true)::uuid);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS stores_tenant_isolation ON stores;")
    op.execute("ALTER TABLE stores NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE stores DISABLE ROW LEVEL SECURITY;")

    app_db_user = os.environ.get("APP_DB_USER", "sajilo_app")
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {app_db_user};")