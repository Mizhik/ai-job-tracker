from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.app.applications import ApplicationService, DeleteApplicationCommand
from backend.core.errors import ApplicationNotFoundError
from backend.core.user import User


@inject
async def delete_application(
    application_id: UUID,
    current_user: User = Depends(require_active_user),
    application_service: ApplicationService = Depends(Provide["application_service"]),
) -> None:
    try:
        await application_service.delete_application(
            DeleteApplicationCommand(
                application_id=application_id,
                user_id=current_user.id,
            )
        )
    except ApplicationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
