from datetime import datetime, timezone
import logging
import httpx
from uuid import UUID

from asyncpg import Pool
from backend.app.admin.queries import AdminQueriesService
from backend.core.repository.admin_repository import AdminUserReadModel
from backend.infrastructure.postgres.admin_repository import AsyncpgAdminRepository
from backend.infrastructure.postgres.pool.create import create_pool
from backend.infrastructure.postgres.pool.settings import DBSettings

logger = logging.getLogger(__name__)


class AdminBotService:
    def __init__(
        self,
        api_base_url: str,
        db_settings: DBSettings | None = None,
        admin_queries_service: AdminQueriesService | None = None,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.db_settings = db_settings
        self._admin_queries_service = admin_queries_service
        self._pool: Pool | None = None

    async def _close_and_reset_pool(self):
        if self._pool is not None:
            try:
                await self._pool.close()
            except Exception as e:
                logger.debug("Error closing pool during reset: %s", str(e))
            self._pool = None

    async def _get_queries_service(self) -> AdminQueriesService | None:
        if self._admin_queries_service:
            return self._admin_queries_service

        if not self.db_settings:
            return None

        if self._pool is not None:
            if getattr(self._pool, "_closed", False):
                await self._close_and_reset_pool()

        if self._pool is None:
            try:
                self._pool = await create_pool(self.db_settings)
            except Exception as e:
                logger.debug("Dynamic DB connection attempt failed: %s", str(e))
                await self._close_and_reset_pool()
                return None

        admin_repo = AsyncpgAdminRepository(self._pool)
        return AdminQueriesService(admin_repo)

    async def close(self):
        await self._close_and_reset_pool()

    async def check_api_health(self) -> tuple[bool, str]:
        health_url = f"{self.api_base_url}/openapi.json"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return True, "Available"
                return False, f"Unavailable (HTTP {response.status_code})"
        except Exception as e:
            logger.debug("API health check failed: %s", str(e))
            return False, "Unavailable"

    async def check_db_health(self) -> tuple[bool, str]:
        q_service = await self._get_queries_service()
        if not q_service:
            return False, "Unavailable"
        try:
            _ = await q_service.get_total_users_count()
            return True, "Available"
        except Exception as e:
            logger.debug("DB health check failed: %s", str(e))
            await self._close_and_reset_pool()
            return False, "Unavailable"

    async def get_system_status(self) -> dict:
        api_ok, api_status = await self.check_api_health()
        db_ok, db_status = await self.check_db_health()

        check_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        total_users = "N/A"
        if db_ok:
            q_service = await self._get_queries_service()
            if q_service:
                try:
                    count = await q_service.get_total_users_count()
                    total_users = str(count)
                except Exception:
                    await self._close_and_reset_pool()
                    total_users = "N/A"

        return {
            "api_status": api_status,
            "db_status": db_status,
            "check_time": check_time,
            "total_users": total_users,
        }

    async def get_users_page(self, page: int = 1, page_size: int = 10) -> tuple[list[AdminUserReadModel], int, int]:
        q_service = await self._get_queries_service()
        if not q_service:
            raise RuntimeError("Database unavailable")
        try:
            return await q_service.get_paginated_users(page=page, page_size=page_size)
        except Exception:
            await self._close_and_reset_pool()
            raise RuntimeError("Database unavailable")

    async def get_user_detail(self, user_id: UUID) -> AdminUserReadModel | None:
        q_service = await self._get_queries_service()
        if not q_service:
            raise RuntimeError("Database unavailable")
        try:
            return await q_service.get_user_detail(user_id)
        except Exception:
            await self._close_and_reset_pool()
            raise RuntimeError("Database unavailable")
