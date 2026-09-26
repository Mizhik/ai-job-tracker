import enum
from dataclasses import dataclass
from uuid import UUID

from .base import Base


class ApplicationStatus(enum.Enum):
    NEW = "new"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


@dataclass(kw_only=True)
class Application(Base):
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    notes: str | None = None
