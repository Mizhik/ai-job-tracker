from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.schemas.user import UserCreateRequest, UserResponse
from backend.app.users.service import UserService
from backend.core.errors import UserAlreadyExistsException


@inject
async def register_user(
    user_create_request: UserCreateRequest,
    user_service: UserService = Depends(Provide["user_service"]),
) -> UserResponse:
    command = user_create_request.to_command()

    try:
        user = await user_service.register_user(command)
    except UserAlreadyExistsException as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.detail,
        )

    return UserResponse.from_user(user)
