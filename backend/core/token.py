import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from backend.core.errors import TokenIsExpiredError


class DecodedAccessToken(BaseModel):
    email: EmailStr
    expires_at: datetime.datetime
    session_id: UUID | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.datetime.now(datetime.timezone.utc)

    def validate(self) -> None:
        if self.is_expired:
            raise TokenIsExpiredError()
