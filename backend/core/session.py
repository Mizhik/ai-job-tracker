from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.core.base import Base


@dataclass(kw_only=True)
class UserSession(Base):
    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
