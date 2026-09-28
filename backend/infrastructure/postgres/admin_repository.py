from uuid import UUID
from asyncpg import Pool

from backend.core.repository.admin_repository import AdminRepository, AdminUserReadModel


class AsyncpgAdminRepository(AdminRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def get_total_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users;"
        count = await self._pool.fetchval(query)
        return count or 0

    async def get_paginated_users(self, limit: int, offset: int) -> list[AdminUserReadModel]:
        query = """
            SELECT id, email, created_at, is_active
            FROM users
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
        """
        rows = await self._pool.fetch(query, limit, offset)
        return [self._row_to_read_model(row) for row in rows]

    async def get_user_by_id(self, user_id: UUID) -> AdminUserReadModel | None:
        query = """
            SELECT id, email, created_at, is_active
            FROM users
            WHERE id = $1::UUID
        """
        row = await self._pool.fetchrow(query, user_id)
        if row:
            return self._row_to_read_model(row)
        return None

    def _row_to_read_model(self, row) -> AdminUserReadModel:
        return AdminUserReadModel(
            id=row["id"],
            email=row["email"],
            created_at=row["created_at"],
            is_active=row["is_active"],
        )
