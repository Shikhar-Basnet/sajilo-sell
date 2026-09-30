import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_db, require_role, set_admin_context, invalidate_user
from app.core.audit import log_action
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.store import Store
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.schemas.store import StoreOut, StoreRejectRequest
from app.schemas.user import UserOut, UserSetActiveRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stores", response_model=list[StoreOut])
async def list_stores(
    status_filter: Literal["pending", "approved", "rejected"] | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_admin_db),
):
    """Full visibility into every store regardless of status —
    get_admin_db sets app.is_admin so the RLS admin-bypass clause
    applies; without it, RLS would still scope this to zero rows."""
    query = select(Store).order_by(Store.created_at.desc())
    if status_filter:
        query = query.where(Store.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/stores/{store_id}/approve", response_model=StoreOut)
async def approve_store(
    store_id: uuid.UUID,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_admin_db),
):
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    store.status = "approved"
    store.rejection_reason = None
    await db.flush()
    await log_action(
        db, table_name="stores", record_id=str(store.id), action="APPROVE",
        actor_id=str(admin.id), changes={"status": "approved"},
    )
    await db.commit()

    await set_admin_context(db)
    await db.refresh(store)
    return store


@router.post("/stores/{store_id}/reject", response_model=StoreOut)
async def reject_store(
    store_id: uuid.UUID,
    payload: StoreRejectRequest,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_admin_db),
):
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    store.status = "rejected"
    store.rejection_reason = payload.reason
    await db.flush()
    await log_action(
        db, table_name="stores", record_id=str(store.id), action="REJECT",
        actor_id=str(admin.id), changes={"status": "rejected", "reason": payload.reason},
    )
    await db.commit()

    await set_admin_context(db)
    await db.refresh(store)
    return store


@router.get("/users", response_model=list[UserOut])
async def list_users(
    role_filter: Literal["admin", "seller", "customer"] | None = Query(default=None, alias="role"),
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """users has no RLS policy — not tenant-scoped data — so this uses
    the plain get_db session; access control is entirely require_role."""
    query = select(User).order_by(User.created_at.desc())
    if role_filter:
        query = query.where(User.role == role_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/users/{user_id}/set-active", response_model=UserOut)
async def set_user_active(
    user_id: uuid.UUID,
    payload: UserSetActiveRequest,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't deactivate your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = payload.is_active
    await db.flush()
    await log_action(
        db, table_name="users", record_id=str(user.id),
        action="ACTIVATE" if payload.is_active else "DEACTIVATE",
        actor_id=str(admin.id), changes={"is_active": payload.is_active},
    )
    await db.commit()
    invalidate_user(user.id)
    await db.refresh(user)
    return user


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=50, le=200),
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return result.scalars().all()