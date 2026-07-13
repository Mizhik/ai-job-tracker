from dataclasses import dataclass
from uuid import UUID

from fastapi.exceptions import ValidationException

from backend.core.errors import NotEnoughPermissionsError, UserNotFoundError
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


@dataclass
class UpdateUserCommand:
    id: UUID
    current_user: User
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None

    def has_update_data(self) -> bool:
        return any(
            [
                self.email is not None,
                self.first_name is not None,
                self.last_name is not None,
            ]
        )

    def apply_updates(self, user: User) -> None:
        if self.email is not None:
            user.email = self.email
        if self.first_name is not None:
            user.first_name = self.first_name
        if self.last_name is not None:
            user.last_name = self.last_name


class UpdateUserCommandHandler:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def handle(self, command: UpdateUserCommand) -> User:
        if not command.has_update_data():
            raise ValidationException("No data provided for update")

        existing_user = await self._user_repository.get_by_id(command.id)

        if not existing_user:
            raise UserNotFoundError(
                f"User with ID {command.id} does not exist"
            )

        if existing_user.id != command.current_user.id:
            raise NotEnoughPermissionsError()

        command.apply_updates(existing_user)
        await self._user_repository.update(existing_user)

        return existing_user
