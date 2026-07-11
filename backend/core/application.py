import enum
from uuid import UUID

from .base import Base


class ApplicationStatus(enum.Enum):
    NEW = "new"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class Application(Base):
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    notes: str | None = None