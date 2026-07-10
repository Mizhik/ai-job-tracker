from backend.app.users.commands.delete_user import DeleteUserCommand, DeleteUserCommandHandler
from backend.app.users.commands.register_user import (
    RegisterUserCommand,
    RegisterUserCommandHandler,
)
from backend.app.users.commands.update_user import (
    UpdateUserCommand,
    UpdateUserCommandHandler,
)
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


class UserService:

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ):
        self._register_users = RegisterUserCommandHandler(
            user_repository, password_hasher
        )
        self._update_users = UpdateUserCommandHandler(user_repository)
        self._delete_users = DeleteUserCommandHandler(user_repository)

    async def register_user(self, command: RegisterUserCommand) -> User:
        return await self._register_users.handle(command)

    async def update_user(self, command: UpdateUserCommand) -> User:
        return await self._update_users.handle(command)

    async def delete_user(self, command: DeleteUserCommand) -> None:
        return await self._delete_users.handle(command)
