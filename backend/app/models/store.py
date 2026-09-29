import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Business verification details, checked by an admin before approval.
    legal_business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pan_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # "pending" (default, awaiting admin review) | "approved" | "rejected".
    # Only approved stores are visible via the stores_public_read RLS policy.
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    # Set by an admin on rejection, shown to the seller, cleared on resubmit.
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)