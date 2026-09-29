from uuid import UUID

from backend.core.repository.admin_repository import AdminRepository, AdminUserReadModel


class AdminQueriesService:
    def __init__(self, admin_repository: AdminRepository):
        self._admin_repo = admin_repository

    async def get_total_users_count(self) -> int:
        return await self._admin_repo.get_total_users_count()

    async def get_paginated_users(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[AdminUserReadModel], int, int]:
        """
        Returns (users, total_count, total_pages).
        """
        if page < 1:
            page = 1

        total_count = await self._admin_repo.get_total_users_count()
        if total_count == 0:
            return [], 0, 0

        total_pages = (total_count + page_size - 1) // page_size
        if page > total_pages:
            page = total_pages

        offset = (page - 1) * page_size
        users = await self._admin_repo.get_paginated_users(limit=page_size, offset=offset)
        return users, total_count, total_pages

    async def get_user_detail(self, user_id: UUID) -> AdminUserReadModel | None:
        return await self._admin_repo.get_user_by_id(user_id)
