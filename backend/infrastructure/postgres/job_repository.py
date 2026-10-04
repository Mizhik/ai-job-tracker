from __future__ import annotations
from uuid import UUID
from asyncpg import Pool

from backend.core.application import ApplicationStatus, ApplicationSummary
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
            SELECT
                j.id, j.user_id, j.title, j.company, j.description, j.location,
                j.salary_min, j.salary_max, j.currency, j.salary_period,
                j.technologies, j.source_url, j.source, j.created_at, j.updated_at,
                a.id AS app_id,
                a.status AS app_status,
                a.applied_at AS app_applied_at
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND j.user_id = a.user_id
            WHERE j.id = $1::UUID AND j.user_id = $2::UUID
        """
        row = await self._pool.fetchrow(query, job_id, user_id)
        if row:
            data = dict(row)
            app_id = data.pop("app_id", None)
            app_status = data.pop("app_status", None)
            app_applied_at = data.pop("app_applied_at", None)

            application_summary = None
            if app_id is not None and app_status is not None and app_applied_at is not None:
                application_summary = ApplicationSummary(
                    id=app_id,
                    status=ApplicationStatus(app_status),
                    applied_at=app_applied_at,
                )

            return Job(**data, application=application_summary)
        return None

    async def list_and_count(
        self,
        user_id: UUID,
        q: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        where_conditions = ["j.user_id = $1::UUID"]
        params: list[object] = [user_id]
        param_idx = 2

        if q and q.strip():
            escaped_q = _escape_like_pattern(q.strip())
            pattern = f"%{escaped_q}%"
            where_conditions.append(
                f"(j.title ILIKE ${param_idx} ESCAPE '\\' OR j.company ILIKE ${param_idx} ESCAPE '\\')"
            )
            params.append(pattern)
            param_idx += 1

        if status and status.strip():
            st_clean = status.strip().lower()
            if st_clean == "saved":
                where_conditions.append("a.id IS NULL")
            else:
                where_conditions.append(f"a.status = ${param_idx}")
                params.append(st_clean)
                param_idx += 1

        where_clause = " WHERE " + " AND ".join(where_conditions)

        count_query = f"""
            SELECT COUNT(*)
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND j.user_id = a.user_id
            {where_clause}
        """
        total = await self._pool.fetchval(count_query, *params)

        items_query = f"""
            SELECT
                j.id, j.user_id, j.title, j.company, j.description, j.location,
                j.salary_min, j.salary_max, j.currency, j.salary_period,
                j.technologies, j.source_url, j.source, j.created_at, j.updated_at,
                a.id AS app_id,
                a.status AS app_status,
                a.applied_at AS app_applied_at
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND j.user_id = a.user_id
            {where_clause}
            ORDER BY j.created_at DESC, j.id DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        items_params = params + [limit, offset]
        rows = await self._pool.fetch(items_query, *items_params)

        jobs: list[Job] = []
        for row in rows:
            data = dict(row)
            app_id = data.pop("app_id", None)
            app_status = data.pop("app_status", None)
            app_applied_at = data.pop("app_applied_at", None)

            application_summary = None
            if app_id is not None and app_status is not None and app_applied_at is not None:
                application_summary = ApplicationSummary(
                    id=app_id,
                    status=ApplicationStatus(app_status),
                    applied_at=app_applied_at,
                )

            jobs.append(Job(**data, application=application_summary))

        return jobs, int(total or 0)

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
