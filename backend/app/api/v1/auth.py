import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, set_tenant_context
from app.core.audit import log_action
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.store import Store
from app.models.user import User
from app.schemas.store import SellerRegister, SellerRegisterOut
from app.schemas.token import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/customer", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_customer(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Customers can browse storefronts and, in a future step, place
    orders. No approval step — active immediately."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role="customer")
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    await log_action(db, table_name="users", record_id=str(user.id), action="CREATE", actor_id=str(user.id))
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/register/seller", response_model=SellerRegisterOut, status_code=status.HTTP_201_CREATED)
async def register_seller(payload: SellerRegister, db: AsyncSession = Depends(get_db)):
    """
    Sellers register with shop details in one step. The account can log
    in immediately, but the store is created with status "pending" and
    stays invisible to the public until an admin approves it via
    POST /admin/stores/{id}/approve.
    """
    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role="seller")
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # RLS's WITH CHECK on stores requires owner_id to match
    # app.current_user_id — set it now, in the same transaction, so the
    # insert below is permitted for the user we just created.
    await set_tenant_context(db, user.id)

    store = Store(owner_id=user.id, status="pending", **payload.store.model_dump())
    db.add(store)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store slug already taken")

    await log_action(db, table_name="users", record_id=str(user.id), action="CREATE", actor_id=str(user.id))
    await log_action(db, table_name="stores", record_id=str(store.id), action="CREATE", actor_id=str(user.id))
    await db.commit()

    await db.refresh(user)
    await set_tenant_context(db, user.id)
    await db.refresh(store)
    return SellerRegisterOut(user=user, store=store)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled, please contact your administrator")

    return TokenPair(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = token_payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenPair(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Lets the frontend know who's logged in and what role they have,
    without decoding the JWT client-side."""
    return current_user