from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    table_name: str,
    record_id: str,
    action: str,
    actor_id: str | None = None,
    changes: dict[str, Any] | None = None,
) -> None:
    """
    Call this inside the same transaction as the actual DB change,
    e.g. right before commit in a create/update/delete endpoint.
    """
    entry = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    )
    db.add(entry)
    await db.flush()