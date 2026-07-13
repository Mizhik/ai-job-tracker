from dataclasses import dataclass
from uuid import UUID

from backend.core.errors import JobNotFoundError
from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class GetJobByIdQuery:
    job_id: UUID


class GetJobByIdQueryHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, query: GetJobByIdQuery) -> Job:
        job = await self._job_repository.get_by_id(query.job_id)
        if job is None:
            raise JobNotFoundError()
        return job
