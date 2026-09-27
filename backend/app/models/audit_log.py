import uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """
    Generic audit trail. Every model that needs auditing writes a row here
    via app.core.audit.log_action() rather than getting its own bespoke
    history table.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)