from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(kw_only=True)
class AdminUserReadModel:
    id: UUID
    email: str
    created_at: datetime
    is_active: bool


class AdminRepository(ABC):
    @abstractmethod
    async def get_total_users_count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_paginated_users(self, limit: int, offset: int) -> list[AdminUserReadModel]:
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> AdminUserReadModel | None:
        raise NotImplementedError
