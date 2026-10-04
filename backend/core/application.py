import enum
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .base import Base


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass(kw_only=True)
class ApplicationSummary:
    id: UUID
    status: ApplicationStatus
    applied_at: datetime


@dataclass(kw_only=True)
class Application(Base):
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    applied_at: datetime
    notes: str | None = None
