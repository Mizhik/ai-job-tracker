from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from backend.core.errors import JobNotFoundError
from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


UNSET: Any = object()


@dataclass
class UpdateJobCommand:
    job_id: UUID
    user_id: UUID
    title: Any = UNSET
    company: Any = UNSET
    description: Any = UNSET
    location: Any = UNSET
    salary_min: Any = UNSET
    salary_max: Any = UNSET
    currency: Any = UNSET
    salary_period: Any = UNSET
    technologies: Any = UNSET
    source_url: Any = UNSET
    source: Any = UNSET


class UpdateJobCommandHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, command: UpdateJobCommand) -> Job:
        existing = await self._job_repository.get_by_id(command.job_id, command.user_id)
        if existing is None:
            raise JobNotFoundError()

        updated_job = Job(
            id=existing.id,
            user_id=existing.user_id,
            title=existing.title if command.title is UNSET else command.title,
            company=existing.company if command.company is UNSET else command.company,
            description=existing.description if command.description is UNSET else command.description,
            location=existing.location if command.location is UNSET else command.location,
            salary_min=existing.salary_min if command.salary_min is UNSET else command.salary_min,
            salary_max=existing.salary_max if command.salary_max is UNSET else command.salary_max,
            currency=existing.currency if command.currency is UNSET else command.currency,
            salary_period=existing.salary_period if command.salary_period is UNSET else command.salary_period,
            technologies=existing.technologies if command.technologies is UNSET else command.technologies,
            source_url=existing.source_url if command.source_url is UNSET else command.source_url,
            source=existing.source if command.source is UNSET else command.source,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        updated_job.validate()

        success = await self._job_repository.update(updated_job)
        if not success:
            raise JobNotFoundError()

        return updated_job
