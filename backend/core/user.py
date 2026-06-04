from .base import Base


class User(Base):
    email: str
    hashed_password: str
    first_name: str | None = None
    last_name: str | None = None
    telegram_chat_id: int | None = None
    is_active: bool = True
