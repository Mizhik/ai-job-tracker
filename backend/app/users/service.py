from backend.app.users.commands.register_user import (
    RegisterUserCommand,
    RegisterUserCommandHandler,
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

    async def register_user(self, command: RegisterUserCommand) -> User:
        return await self._register_users.handle(command)
