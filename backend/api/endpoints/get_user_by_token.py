from typing import Annotated
from dependency_injector.wiring import inject
from fastapi import Depends

from backend.api.dependencies import require_active_user
from backend.api.schemas.user import UserResponse
from backend.core.user import User


async def get_user_by_token(
    current_user: Annotated[User, Depends(require_active_user)],
) -> UserResponse:

    return UserResponse.from_user(current_user)
