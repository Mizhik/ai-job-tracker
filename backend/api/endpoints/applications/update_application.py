from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.application import ApplicationResponse, ApplicationUpdateInput
from backend.app.applications import ApplicationService, UpdateApplicationCommand
from backend.core.errors import ApplicationNotFoundError
from backend.core.user import User


@inject
async def update_application(
    application_id: UUID,
    input_data: ApplicationUpdateInput,
    current_user: User = Depends(require_active_user),
    application_service: ApplicationService = Depends(Provide["application_service"]),
) -> ApplicationResponse:
    try:
        update_notes = "notes" in input_data.model_fields_set
        app = await application_service.update_application(
            UpdateApplicationCommand(
                application_id=application_id,
                user_id=current_user.id,
                status=input_data.status,
                notes=input_data.notes,
                applied_at=input_data.applied_at,
                update_notes=update_notes,
            )
        )
        return ApplicationResponse.model_validate(app)
    except ApplicationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
