from uuid import UUID

from .base import Base


class Resume(Base):
    user_id: UUID
    filename: str
    file_path: str
