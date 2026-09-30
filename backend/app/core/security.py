# backend/app/core/security.py
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.concurrency import run_in_threadpool
from jose import jwt
from passlib.context import CryptContext

from app.config import settings

# 11 rounds ≈ half the CPU of the default 12 and still above OWASP's minimum.
# Existing hashes keep verifying (rounds are stored in each hash).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=11)

# At most 2 concurrent hashes so a burst of logins can't starve the 0.25 vCPU.
_hash_slots = asyncio.Semaphore(2)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def hash_password_async(password: str) -> str:
    async with _hash_slots:
        return await run_in_threadpool(hash_password, password)


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    async with _hash_slots:
        return await run_in_threadpool(verify_password, plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])