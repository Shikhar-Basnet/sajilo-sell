import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    created_at: datetime