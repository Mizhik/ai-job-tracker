from __future__ import annotations
from uuid import UUID
from asyncpg import Pool

from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


def _escape_like_pattern(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class AsyncpgJobRepository(JobRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create(self, job: Job) -> None:
        query = """
            INSERT INTO jobs (
                id, user_id, title, company, description, location,
                salary_min, salary_max, currency, salary_period,
                technologies, source_url, source, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        """
        await self._pool.execute(
            query,
            job.id,
            job.user_id,
            job.title,
            job.company,
            job.description,
            job.location,
            job.salary_min,
            job.salary_max,
            job.currency,
            job.salary_period,
            job.technologies,
            job.source_url,
            job.source,
            job.created_at,
            job.updated_at,
        )

    async def get_by_id(self, job_id: UUID, user_id: UUID) -> Job | None:
        query = """
            SELECT *
            FROM jobs
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        row = await self._pool.fetchrow(query, job_id, user_id)
        if row:
            return Job(**dict(row))
        return None

    async def list(self, user_id: UUID) -> list[Job]:
        query = """
            SELECT *
            FROM jobs
            WHERE user_id = $1::UUID
            ORDER BY created_at DESC
        """
        rows = await self._pool.fetch(query, user_id)
        return [Job(**dict(row)) for row in rows]

    async def list_and_count(
        self,
        user_id: UUID,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        if q and q.strip():
            escaped_q = _escape_like_pattern(q.strip())
            pattern = f"%{escaped_q}%"
            count_query = """
                SELECT COUNT(*)
                FROM jobs
                WHERE user_id = $1::UUID
                  AND (title ILIKE $2 ESCAPE '\\' OR company ILIKE $2 ESCAPE '\\')
            """
            items_query = """
                SELECT *
                FROM jobs
                WHERE user_id = $1::UUID
                  AND (title ILIKE $2 ESCAPE '\\' OR company ILIKE $2 ESCAPE '\\')
                ORDER BY created_at DESC, id DESC
                LIMIT $3 OFFSET $4
            """
            total = await self._pool.fetchval(count_query, user_id, pattern)
            rows = await self._pool.fetch(items_query, user_id, pattern, limit, offset)
        else:
            count_query = """
                SELECT COUNT(*)
                FROM jobs
                WHERE user_id = $1::UUID
            """
            items_query = """
                SELECT *
                FROM jobs
                WHERE user_id = $1::UUID
                ORDER BY created_at DESC, id DESC
                LIMIT $2 OFFSET $3
            """
            total = await self._pool.fetchval(count_query, user_id)
            rows = await self._pool.fetch(items_query, user_id, limit, offset)

        return [Job(**dict(row)) for row in rows], int(total or 0)

    async def update(self, job: Job) -> bool:
        query = """
            UPDATE jobs
            SET title = $3,
                company = $4,
                description = $5,
                location = $6,
                salary_min = $7,
                salary_max = $8,
                currency = $9,
                salary_period = $10,
                technologies = $11,
                source_url = $12,
                source = $13,
                updated_at = $14
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        res = await self._pool.execute(
            query,
            job.id,
            job.user_id,
            job.title,
            job.company,
            job.description,
            job.location,
            job.salary_min,
            job.salary_max,
            job.currency,
            job.salary_period,
            job.technologies,
            job.source_url,
            job.source,
            job.updated_at,
        )
        return res == "UPDATE 1"

    async def delete(self, job_id: UUID, user_id: UUID) -> bool:
        query = """
            DELETE FROM jobs
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        res = await self._pool.execute(query, job_id, user_id)
        return res == "DELETE 1"
