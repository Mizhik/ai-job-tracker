from __future__ import annotations
from uuid import UUID
import asyncpg
from asyncpg import Pool

from backend.core.application import Application, ApplicationStatus
from backend.core.errors import ApplicationAlreadyExistsError
from backend.core.repository.application_repository import ApplicationRepository


class AsyncpgApplicationRepository(ApplicationRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create(self, application: Application) -> None:
        query = """
            INSERT INTO applications (
                id, user_id, job_id, status, notes, applied_at, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        status_str = (
            application.status.value
            if isinstance(application.status, ApplicationStatus)
            else str(application.status)
        )
        try:
            await self._pool.execute(
                query,
                application.id,
                application.user_id,
                application.job_id,
                status_str,
                application.notes,
                application.applied_at,
                application.created_at,
                application.updated_at,
            )
        except asyncpg.UniqueViolationError:
            raise ApplicationAlreadyExistsError()

    async def get_by_id(self, application_id: UUID, user_id: UUID) -> Application | None:
        query = """
            SELECT id, user_id, job_id, status, notes, applied_at, created_at, updated_at
            FROM applications
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        row = await self._pool.fetchrow(query, application_id, user_id)
        if row:
            data = dict(row)
            data["status"] = ApplicationStatus(data["status"])
            return Application(**data)
        return None

    async def get_by_job_id(self, job_id: UUID, user_id: UUID) -> Application | None:
        query = """
            SELECT id, user_id, job_id, status, notes, applied_at, created_at, updated_at
            FROM applications
            WHERE job_id = $1::UUID AND user_id = $2::UUID
        """
        row = await self._pool.fetchrow(query, job_id, user_id)
        if row:
            data = dict(row)
            data["status"] = ApplicationStatus(data["status"])
            return Application(**data)
        return None

    async def update(self, application: Application) -> bool:
        query = """
            UPDATE applications
            SET status = $3,
                notes = $4,
                applied_at = $5,
                updated_at = $6
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        status_str = (
            application.status.value
            if isinstance(application.status, ApplicationStatus)
            else str(application.status)
        )
        res = await self._pool.execute(
            query,
            application.id,
            application.user_id,
            status_str,
            application.notes,
            application.applied_at,
            application.updated_at,
        )
        return res == "UPDATE 1"

    async def delete(self, application_id: UUID, user_id: UUID) -> bool:
        query = """
            DELETE FROM applications
            WHERE id = $1::UUID AND user_id = $2::UUID
        """
        res = await self._pool.execute(query, application_id, user_id)
        return res == "DELETE 1"
