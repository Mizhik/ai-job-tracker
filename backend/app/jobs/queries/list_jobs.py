from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


class ListJobsQueryHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self) -> list[Job]:
        return await self._job_repository.list()
