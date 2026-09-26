from dataclasses import dataclass
from uuid import UUID

from .base import Base


@dataclass(kw_only=True)
class Resume(Base):
    user_id: UUID
    filename: str
    file_path: str
