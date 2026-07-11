from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class CreateJobCommand:
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


class CreateJobCommandHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def handle(self, command: CreateJobCommand) -> Job:
        job = Job(
            id=uuid4(),
            title=command.title,
            company=command.company,
            description=command.description,
            location=command.location,
            salary_min=command.salary_min,
            salary_max=command.salary_max,
            technologies=command.technologies,
            source_url=command.source_url,
            source=command.source,
            created_at=datetime.now(timezone.utc),
        )
        await self._job_repository.create(job)
        return job
