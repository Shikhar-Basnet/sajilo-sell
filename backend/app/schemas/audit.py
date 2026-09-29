import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    table_name: str
    record_id: str
    action: str
    actor_id: str | None
    changes: dict[str, Any] | None
    created_at: datetime