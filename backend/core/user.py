from backend.core.errors import EmailOrPasswordIncorrectError, UserBlockedError
from .base import Base


class User(Base):
    email: str
    hashed_password: str
    first_name: str | None = None
    last_name: str | None = None
    telegram_chat_id: int | None = None
    is_active: bool = True

    def login(self, password: str, verify_password) -> None:
        if self.is_active is False:
            raise UserBlockedError()
        if not self.hashed_password or not verify_password(
            password, self.hashed_password
        ):
            raise EmailOrPasswordIncorrectError()
