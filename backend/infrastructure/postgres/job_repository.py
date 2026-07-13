from uuid import UUID
from asyncpg import Pool

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


class AsyncpgJobRepository(JobRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create(self, job: Job) -> None:
        query = """
            INSERT INTO jobs (
                id, title, company, description, location,
                salary_min, salary_max, technologies, source_url, source,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """
        await self._pool.execute(
            query,
            job.id,
            job.title,
            job.company,
            job.description,
            job.location,
            job.salary_min,
            job.salary_max,
            job.technologies,
            job.source_url,
            job.source,
            job.created_at,
            job.updated_at,
        )

    async def get_by_id(self, job_id: UUID) -> Job | None:
        query = """
            SELECT *
            FROM jobs
            WHERE id = $1::UUID
        """
        row = await self._pool.fetchrow(query, job_id)
        if row:
            return Job(**dict(row))
        return None

    async def list(self) -> list[Job]:
        query = """
            SELECT *
            FROM jobs
            ORDER BY created_at DESC
        """
        rows = await self._pool.fetch(query)
        return [Job(**dict(row)) for row in rows]
