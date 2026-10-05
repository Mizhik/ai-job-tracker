from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from backend.core.application import Application


class ApplicationRepository(ABC):
    @abstractmethod
    async def create(self, application: Application) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, application_id: UUID, user_id: UUID) -> Application | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_job_id(self, job_id: UUID, user_id: UUID) -> Application | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, application: Application) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, application_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError
