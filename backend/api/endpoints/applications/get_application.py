from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.application import ApplicationResponse
from backend.app.applications import ApplicationService, GetApplicationByIdQuery
from backend.core.errors import ApplicationNotFoundError
from backend.core.user import User


@inject
async def get_application(
    application_id: UUID,
    current_user: User = Depends(require_active_user),
    application_service: ApplicationService = Depends(Provide["application_service"]),
) -> ApplicationResponse:
    try:
        app = await application_service.get_application_by_id(
            GetApplicationByIdQuery(
                application_id=application_id,
                user_id=current_user.id,
            )
        )
        return ApplicationResponse.model_validate(app)
    except ApplicationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
