from dataclasses import dataclass
from uuid import UUID

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class ListJobsQuery:
    user_id: UUID


class ListJobsQueryHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, query: ListJobsQuery) -> list[Job]:
        return await self._job_repository.list(query.user_id)
