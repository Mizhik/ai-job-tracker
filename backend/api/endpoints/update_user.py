from typing import Annotated
from uuid import UUID
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.user import UserUpdateRequest, UserResponse
from backend.app.users.service import UserService
from backend.core.errors import NotEnoughPermissionsError, UserAlreadyExistsException
from backend.core.user import User


@inject
async def update_user(
    user_id: UUID,
    user_update_request: UserUpdateRequest,
    current_user: Annotated[User, Depends(require_active_user)],
    user_service: UserService = Depends(Provide["user_service"]),
) -> UserResponse:
    command = user_update_request.to_command(user_id, current_user)

    try:
        user = await user_service.update_user(command)
    except (UserAlreadyExistsException, NotEnoughPermissionsError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.detail,
        )

    return UserResponse.from_user(user)
