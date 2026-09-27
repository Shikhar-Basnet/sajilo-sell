from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_db, set_tenant_context
from app.core.audit import log_action
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StoreOut

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: StoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    existing = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a store")

    store = Store(owner_id=current_user.id, name=payload.name, slug=payload.slug)
    db.add(store)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store slug already taken")

    await log_action(
        db, table_name="stores", record_id=str(store.id), action="CREATE", actor_id=str(current_user.id)
    )
    await db.commit()

    # commit() ended the transaction, which reset app.current_user_id —
    # re-apply it before refresh(), which opens a new transaction and
    # must pass the RLS policy's check again.
    await set_tenant_context(db, current_user.id)
    await db.refresh(store)
    return store


@router.get("/me", response_model=StoreOut)
async def get_my_store(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No store found for this user")
    return store