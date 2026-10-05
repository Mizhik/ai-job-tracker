from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.application import ApplicationCreateInput, ApplicationResponse
from backend.app.applications import ApplicationService, CreateApplicationCommand
from backend.core.errors import ApplicationAlreadyExistsError, JobNotFoundError
from backend.core.user import User


@inject
async def create_application(
    job_id: UUID,
    input_data: ApplicationCreateInput,
    current_user: User = Depends(require_active_user),
    application_service: ApplicationService = Depends(Provide["application_service"]),
) -> ApplicationResponse:
    try:
        app = await application_service.create_application(
            CreateApplicationCommand(
                user_id=current_user.id,
                job_id=job_id,
                status=input_data.status,
                notes=input_data.notes,
                applied_at=input_data.applied_at,
            )
        )
        return ApplicationResponse.model_validate(app)
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
    except ApplicationAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        )
