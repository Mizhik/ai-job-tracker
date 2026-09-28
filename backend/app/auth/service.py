from datetime import timedelta

from backend.app.auth.commands.login import LoginCommand, LoginCommandHandler, LoginResult
from backend.app.auth.commands.logout import LogoutCommand, LogoutCommandHandler
from backend.app.auth.commands.refresh_token import (
    RefreshTokenCommand,
    RefreshTokenCommandHandler,
    RefreshResult,
)
from backend.app.auth.queries.get_user_by_token import (
    GetUserByTokenQuery,
    GetUserByTokenQueryHandler,
)
from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.abc.session_token_service import SessionTokenService
from backend.core.repository.user_repository import UserRepository
from backend.core.repository.user_session_repository import UserSessionRepository
from backend.core.user import User


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        access_token_generator: AccessTokenGenerator,
        user_session_repository: UserSessionRepository,
        session_token_service: SessionTokenService,
        access_token_expire_delta: timedelta | None = None,
    ):
        self._user_session_repository = user_session_repository
        self._session_token_service = session_token_service

        self._login = LoginCommandHandler(
            access_token_generator=access_token_generator,
            user_repository=user_repository,
            password_hasher=password_hasher,
            user_session_repository=user_session_repository,
            session_token_service=session_token_service,
            expires_delta=access_token_expire_delta,
        )
        self._get_user_by_token_handler = GetUserByTokenQueryHandler(
            access_token_service=access_token_generator,
            user_repository=user_repository,
            user_session_repository=user_session_repository,
        )
        self._refresh_token_handler = RefreshTokenCommandHandler(
            user_session_repository=user_session_repository,
            user_repository=user_repository,
            access_token_generator=access_token_generator,
            session_token_service=session_token_service,
            access_token_expire_delta=access_token_expire_delta,
        )
        self._logout_handler = LogoutCommandHandler(
            user_session_repository=user_session_repository,
            session_token_service=session_token_service,
        )

    async def login(self, command: LoginCommand) -> LoginResult:
        return await self._login(command)

    async def refresh_token(self, command: RefreshTokenCommand) -> RefreshResult:
        return await self._refresh_token_handler(command)

    async def logout(self, command: LogoutCommand) -> None:
        await self._logout_handler(command)

    async def get_user_by_token(self, query: GetUserByTokenQuery) -> User:
        return await self._get_user_by_token_handler(query)
