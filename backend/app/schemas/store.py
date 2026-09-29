import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserOut


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=2000)
    contact_phone: str | None = Field(default=None, max_length=50)
    # Verified by an admin before approval.
    legal_business_name: str = Field(min_length=2, max_length=255)
    owner_full_name: str = Field(min_length=2, max_length=255)
    pan_number: str = Field(min_length=5, max_length=50)


class StoreUpdate(BaseModel):
    """Partial update — used by sellers editing their own store, including
    resubmission after a rejection. Slug is deliberately not editable
    here (it's the storefront URL, changing it would break existing links)."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    contact_phone: str | None = Field(default=None, max_length=50)
    legal_business_name: str | None = Field(default=None, min_length=2, max_length=255)
    owner_full_name: str | None = Field(default=None, min_length=2, max_length=255)
    pan_number: str | None = Field(default=None, min_length=5, max_length=50)


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    contact_phone: str | None
    legal_business_name: str | None
    owner_full_name: str | None
    pan_number: str | None
    status: Literal["pending", "approved", "rejected"]
    rejection_reason: str | None
    created_at: datetime


class StorePublicOut(BaseModel):
    """What an anonymous storefront visitor sees. Only ever populated
    from rows RLS has already filtered to status='approved' — omits id,
    owner_id, and status since none of that is public-facing."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    description: str | None
    contact_phone: str | None
    created_at: datetime


class SellerRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    store: StoreCreate


class SellerRegisterOut(BaseModel):
    user: UserOut
    store: StoreOut


class StoreRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)