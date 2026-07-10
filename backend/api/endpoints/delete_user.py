from typing import Annotated
from uuid import UUID
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.app.users.commands.delete_user import DeleteUserCommand
from backend.app.users.service import UserService
from backend.core.errors import NotEnoughPermissionsError, UserNotFoundError
from backend.core.user import User


@inject
async def delete_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_active_user)],
    user_service: UserService = Depends(Provide["user_service"]),
) -> None:

    try:
        await user_service.delete_user(
            DeleteUserCommand(id=user_id, current_user=current_user)
        )
    except (NotEnoughPermissionsError, UserNotFoundError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.detail,
        )
