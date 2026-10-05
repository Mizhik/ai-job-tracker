from dataclasses import dataclass
from uuid import UUID

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


@dataclass
class ListJobsQuery:
    user_id: UUID
    q: str | None = None
    status: str | None = None
    limit: int = 20
    offset: int = 0


@dataclass
class ListJobsResult:
    items: list[Job]
    total: int
    limit: int
    offset: int


class ListJobsQueryHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, query: ListJobsQuery) -> ListJobsResult:
        items, total = await self._job_repository.list_and_count(
            user_id=query.user_id,
            q=query.q,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        return ListJobsResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
