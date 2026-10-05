from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.core.application import ApplicationStatus


@dataclass
class CreateApplicationCommand:
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None


@dataclass
class UpdateApplicationCommand:
    application_id: UUID
    user_id: UUID
    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None
    update_notes: bool = False


@dataclass
class DeleteApplicationCommand:
    application_id: UUID
    user_id: UUID
