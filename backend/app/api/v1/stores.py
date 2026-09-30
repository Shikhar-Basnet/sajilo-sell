from fastapi import APIRouter, Depends, HTTPException, Response, status   # add Response
from app.core.cache import set_public_cache
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_store, get_tenant_db, require_role, set_tenant_context
from app.core.audit import log_action
from app.database import get_db
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StoreOut, StorePublicOut, StoreUpdate

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("/me", response_model=StoreOut)
async def get_my_store(store: Store = Depends(get_owned_store)):
    """Returns the authenticated seller's store."""
    return store


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: StoreCreate,
    current_user: User = Depends(require_role("seller")),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Manual/fallback store creation — the normal path is
    /auth/register/seller, which creates the store as part of
    registration. New stores always start "pending"."""
    existing = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a store")

    store = Store(owner_id=current_user.id, status="pending", **payload.model_dump())
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

    await set_tenant_context(db, current_user.id)
    await db.refresh(store)
    return store


@router.patch("/me", response_model=StoreOut)
async def update_my_store(
    payload: StoreUpdate,
    current_user: User = Depends(require_role("seller")),
    db: AsyncSession = Depends(get_tenant_db),
):
    """
    Lets a seller edit their store details. If the store was rejected,
    this also resubmits it — status flips back to "pending" and
    rejection_reason clears, so the admin sees it in the pending queue
    again. Approved stores can't be edited here (business details are
    already verified); contact-support is the intended path for that.
    """
    result = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No store found for this account")

    if store.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your store is already approved. Contact support to change verified business details.",
        )

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(store, field, value)

    was_rejected = store.status == "rejected"
    if was_rejected:
        store.status = "pending"
        store.rejection_reason = None
        changes["status"] = "pending"

    await db.flush()
    await log_action(
        db, table_name="stores", record_id=str(store.id),
        action="RESUBMIT" if was_rejected else "UPDATE",
        actor_id=str(current_user.id), changes=changes,
    )
    await db.commit()

    await set_tenant_context(db, current_user.id)
    await db.refresh(store)
    return store


@router.get("", response_model=list[StorePublicOut])
async def list_public_stores(response: Response, db: AsyncSession = Depends(get_db)):
    set_public_cache(response, s_maxage=60, swr=600)
    result = await db.execute(
        select(Store).where(Store.status == "approved").order_by(Store.created_at.desc())
    )
    return result.scalars().all()


@router.get("/by-slug/{slug}", response_model=StorePublicOut)
async def get_store_by_slug(slug: str, response: Response, db: AsyncSession = Depends(get_db)):
    set_public_cache(response, s_maxage=60, swr=600)
    result = await db.execute(select(Store).where(Store.slug == slug))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store