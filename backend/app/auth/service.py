from backend.app.auth.commands.login import LoginCommand, LoginCommandHandler
from backend.app.auth.queries.get_user_by_token import (
    GetUserByTokenQuery,
    GetUserByTokenQueryHandler,
)
from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User
from backend.infrastructure.settings.auth import AuthSettings


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        access_token_generator: AccessTokenGenerator,
        auth_settings: AuthSettings,
    ):
        self._login = LoginCommandHandler(
            access_token_generator=access_token_generator,
            user_repository=user_repository,
            password_hasher=password_hasher,
            settings=auth_settings,
        )
        self._get_user_by_token_handler = GetUserByTokenQueryHandler(
            access_token_service=access_token_generator,
            user_repository=user_repository,
        )

    async def login(self, command: LoginCommand) -> str:
        return await self._login(command)

    async def get_user_by_token(self, query: GetUserByTokenQuery) -> User:
        return await self._get_user_by_token_handler(query)
