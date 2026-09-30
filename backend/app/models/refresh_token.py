import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """
    One row per issued refresh token. This is what lets refresh tokens be
    revoked and lets the inactivity timeout be enforced server-side —
    neither is possible with a bare stateless JWT. No RLS here: this
    isn't tenant-scoped data and is read during auth, before any tenant
    context exists.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Absolute expiry — reset to now + REFRESH_TOKEN_EXPIRE_DAYS on every
    # rotation, so this only actually gets hit if the token is never used.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Updated on every successful refresh. Compared against
    # REFRESH_TOKEN_INACTIVITY_MINUTES to detect an abandoned session.
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Set on rotation, logout, or reuse-detected revocation. A revoked
    # token being presented again is treated as a signal of token theft.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)