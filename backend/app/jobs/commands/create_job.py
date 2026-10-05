from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class CreateJobCommand:
    user_id: UUID
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: str | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


class CreateJobCommandHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, command: CreateJobCommand) -> Job:
        job = Job(
            id=uuid4(),
            user_id=command.user_id,
            title=command.title,
            company=command.company,
            description=command.description,
            location=command.location,
            salary_min=command.salary_min,
            salary_max=command.salary_max,
            currency=command.currency,
            salary_period=command.salary_period,
            technologies=command.technologies,
            source_url=command.source_url,
            source=command.source,
            created_at=datetime.now(timezone.utc),
        )
        job.validate()
        await self._job_repository.create(job)
        return job
