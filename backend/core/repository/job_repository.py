from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from backend.core.job import Job


class JobRepository(ABC):
    @abstractmethod
    async def create(self, job: Job) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, job_id: UUID, user_id: UUID) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, user_id: UUID) -> list[Job]:
        raise NotImplementedError

    @abstractmethod
    async def list_and_count(
        self,
        user_id: UUID,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, job: Job) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, job_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError
