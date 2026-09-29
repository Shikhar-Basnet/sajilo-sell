import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.store import Store
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control, orthogonal to RLS
    tenant isolation. RLS answers "is this row yours?"; this answers
    "are you the kind of user allowed to do this at all?"

    Raises 403, not 404 — a role check should be upfront that the
    resource/action exists but access is denied, unlike tenant-scoped
    endpoints which 404 on other users' rows to avoid confirming they
    exist.
    """

    async def checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action",
            )
        return current_user

    return checker


async def set_tenant_context(db: AsyncSession, user_id: uuid.UUID) -> None:
    """
    Sets the Postgres session variable RLS tenant-isolation policies
    check, scoped to the current transaction only (set_config's third
    arg = true). Must be called again after any commit(), since
    committing ends the transaction and resets this value.
    """
    await db.execute(
        text("SELECT set_config('app.current_user_id', :uid, true)"),
        {"uid": str(user_id)},
    )


async def set_admin_context(db: AsyncSession) -> None:
    """Flags this DB session as admin so the RLS admin-bypass clause on
    stores/products applies. Also explicitly resets app.current_user_id
    to NULL for this transaction — belt and suspenders alongside the
    nullif() guard in the RLS policies themselves, so this session never
    depends on whatever a previous request left on a pooled connection."""
    await db.execute(text("SELECT set_config('app.is_admin', 'true', true)"))
    await db.execute(text("SELECT set_config('app.current_user_id', '', true)"))

async def get_tenant_db(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncSession:
    """
    Same DB session as get_db, but with app.current_user_id set for this
    transaction. Required for RLS tenant-isolation policies to let the
    request see its own rows.
    """
    await set_tenant_context(db, current_user.id)
    return db


async def get_admin_db(
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncSession:
    """
    Same DB session as get_db, but with app.is_admin set so the RLS
    admin-bypass clause on stores/products applies. require_role("admin")
    has already confirmed the caller's role at the API layer; this
    mirrors that down to the database layer, since RLS is enforced per
    connecting session regardless of app-level role — without this, even
    an admin would be tenant-scoped to zero rows of their own.
    """
    await set_admin_context(db)
    return db


async def get_owned_store(
    current_user: Annotated[User, Depends(require_role("seller"))],
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Store:
    """
    Resolves the current seller's store, or 404s. Shared by every
    product endpoint. require_role("seller") here means customers/admins
    get a clean 403 instead of a confusing 404 when they hit these routes.
    """
    result = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No store found for this account")
    return store