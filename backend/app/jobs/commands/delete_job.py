from dataclasses import dataclass
from uuid import UUID

from backend.core.errors import JobNotFoundError
from backend.core.repository.job_repository import JobRepository


@dataclass
class DeleteJobCommand:
    job_id: UUID
    user_id: UUID


class DeleteJobCommandHandler:
    def __init__(self, job_repository: JobRepository):
        self._job_repository = job_repository

    async def __call__(self, command: DeleteJobCommand) -> None:
        deleted = await self._job_repository.delete(command.job_id, command.user_id)
        if not deleted:
            raise JobNotFoundError()
