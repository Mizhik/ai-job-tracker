from dataclasses import dataclass
from uuid import UUID

from fastapi.exceptions import ValidationException

from backend.core.errors import NotEnoughPermissionsError, UserNotFoundError
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


@dataclass
class DeleteUserCommand:
    id: UUID
    current_user: User


class DeleteUserCommandHandler:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def handle(self, command: DeleteUserCommand) -> None:
        existing_user = await self._user_repository.get_by_id(command.id)

        if not existing_user:
            raise UserNotFoundError(
                f"User with ID {command.id} does not exist"
            )

        if command.id != command.current_user.id:
            raise NotEnoughPermissionsError()

        await self._user_repository.delete(existing_user)
