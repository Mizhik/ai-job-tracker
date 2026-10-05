from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from backend.core.errors import JobNotFoundError
from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class UpdateJobCommand:
    job_id: UUID
    user_id: UUID
    title: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: str | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


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
            title=command.title if command.title is not None else existing.title,
            company=command.company if command.company is not None else existing.company,
            description=command.description if command.description is not None else existing.description,
            location=command.location if command.location is not None else existing.location,
            salary_min=command.salary_min if command.salary_min is not None else existing.salary_min,
            salary_max=command.salary_max if command.salary_max is not None else existing.salary_max,
            currency=command.currency if command.currency is not None else existing.currency,
            salary_period=command.salary_period if command.salary_period is not None else existing.salary_period,
            technologies=command.technologies if command.technologies is not None else existing.technologies,
            source_url=command.source_url if command.source_url is not None else existing.source_url,
            source=command.source if command.source is not None else existing.source,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        updated_job.validate()

        success = await self._job_repository.update(updated_job)
        if not success:
            raise JobNotFoundError()

        return updated_job
