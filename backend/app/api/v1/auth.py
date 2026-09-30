import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, set_tenant_context
from app.config import settings
from app.core.audit import log_action
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    hash_password_async,
    verify_password_async,
)
from app.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.store import Store
from app.models.user import User
from app.schemas.store import SellerRegister, SellerRegisterOut
from app.schemas.token import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# backend/app/api/v1/auth.py
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password_async, verify_password_async,
)

def _token_pair(user: User) -> TokenPair:
    # role/email are UI hints only. The backend still enforces roles on every request.
    return TokenPair(
        access_token=create_access_token(
            subject=str(user.id), extra_claims={"role": user.role, "email": user.email}
        ),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )

async def _issue_token_pair(db: AsyncSession, user_id: uuid.UUID) -> TokenPair:
    """
    Creates a fresh access/refresh pair and a matching RefreshToken row.
    Called on login and on every successful rotation — each call resets
    expires_at forward by REFRESH_TOKEN_EXPIRE_DAYS, which is what lets a
    continuously-active session outlive any single token's nominal
    lifetime.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4()

    db.add(RefreshToken(id=jti, user_id=user_id, expires_at=expires_at, last_used_at=now))
    await db.commit()

    return TokenPair(
        access_token=create_access_token(subject=str(user_id)),
        refresh_token=create_refresh_token(subject=str(user_id), jti=str(jti), expires_at=expires_at),
    )


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

    if user is None or not await verify_password_async(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled, please contact your administrator")
    return _token_pair(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = token_payload.get("jti")
    user_id = token_payload.get("sub")
    if not jti or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(RefreshToken).where(RefreshToken.id == uuid.UUID(jti)))
    stored = result.scalar_one_or_none()

    if stored is None or str(stored.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    now = datetime.now(timezone.utc)

    if stored.revoked_at is not None:
        # This token was already rotated away (or explicitly logged out)
        # and is being presented again — treat as possible theft/replay
        # and kill every other active session for this user too.
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked, please log in again")

    if now > stored.expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again")

    idle_for = now - stored.last_used_at
    if idle_for > timedelta(minutes=settings.REFRESH_TOKEN_INACTIVITY_MINUTES):
        stored.revoked_at = now
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to inactivity, please log in again",
        )

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate: retire this token, issue a fresh one with a renewed
    # expires_at. As long as the gap between uses stays under
    # REFRESH_TOKEN_INACTIVITY_MINUTES, this keeps sliding forward
    # indefinitely — an actively-used session never hits the absolute cap.
    stored.revoked_at = now
    await db.flush()

    return _token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Revokes the refresh token server-side so it can't be replayed even if
    it leaks after this point — clearing it from the browser alone
    doesn't invalidate a JWT. Always returns 204 regardless of whether
    the token was valid, so this endpoint doesn't leak session state.
    """
    try:
        token_payload = decode_token(payload.refresh_token)
        jti = token_payload.get("jti")
        if jti:
            result = await db.execute(select(RefreshToken).where(RefreshToken.id == uuid.UUID(jti)))
            stored = result.scalar_one_or_none()
            if stored is not None and stored.revoked_at is None:
                stored.revoked_at = datetime.now(timezone.utc)
                await db.commit()
    except (JWTError, ValueError):
        pass
    return None


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Lets the frontend know who's logged in and what role they have,
    without decoding the JWT client-side."""
    return current_user