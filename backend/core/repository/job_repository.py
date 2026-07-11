from abc import ABC, abstractmethod
from uuid import UUID

from backend.core.job import Job


class JobRepository(ABC):
    @abstractmethod
    async def create(self, job: Job) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[Job]:
        raise NotImplementedError
