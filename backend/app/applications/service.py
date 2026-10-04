from datetime import datetime, timezone
from uuid import UUID, uuid4

from backend.core.application import Application, ApplicationStatus
from backend.core.errors import (
    ApplicationAlreadyExistsError,
    ApplicationNotFoundError,
    JobNotFoundError,
)
from backend.core.repository.application_repository import ApplicationRepository
from backend.core.repository.job_repository import JobRepository
from .commands import (
    CreateApplicationCommand,
    DeleteApplicationCommand,
    UpdateApplicationCommand,
)
from .queries import GetApplicationByIdQuery


class ApplicationService:
    def __init__(
        self,
        application_repository: ApplicationRepository,
        job_repository: JobRepository,
    ):
        self._application_repository = application_repository
        self._job_repository = job_repository

    async def create_application(
        self, command: CreateApplicationCommand
    ) -> Application:
        job = await self._job_repository.get_by_id(command.job_id, command.user_id)
        if job is None:
            raise JobNotFoundError()

        existing = await self._application_repository.get_by_job_id(
            command.job_id, command.user_id
        )
        if existing is not None:
            raise ApplicationAlreadyExistsError()

        status = command.status or ApplicationStatus.APPLIED
        now = datetime.now(timezone.utc)
        applied_at = command.applied_at or now

        app = Application(
            id=uuid4(),
            user_id=command.user_id,
            job_id=command.job_id,
            status=status,
            notes=command.notes,
            applied_at=applied_at,
            created_at=now,
            updated_at=now,
        )

        await self._application_repository.create(app)
        return app

    async def get_application_by_id(
        self, query: GetApplicationByIdQuery
    ) -> Application:
        app = await self._application_repository.get_by_id(
            query.application_id, query.user_id
        )
        if app is None:
            raise ApplicationNotFoundError()
        return app

    async def update_application(
        self, command: UpdateApplicationCommand
    ) -> Application:
        app = await self._application_repository.get_by_id(
            command.application_id, command.user_id
        )
        if app is None:
            raise ApplicationNotFoundError()

        if command.status is not None:
            app.status = command.status

        if command.applied_at is not None:
            app.applied_at = command.applied_at

        if command.update_notes:
            app.notes = command.notes

        app.updated_at = datetime.now(timezone.utc)

        success = await self._application_repository.update(app)
        if not success:
            raise ApplicationNotFoundError()

        return app

    async def delete_application(
        self, command: DeleteApplicationCommand
    ) -> None:
        success = await self._application_repository.delete(
            command.application_id, command.user_id
        )
        if not success:
            raise ApplicationNotFoundError()
