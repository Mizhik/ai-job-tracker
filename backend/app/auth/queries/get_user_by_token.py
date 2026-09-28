from dataclasses import dataclass
from datetime import datetime, timezone

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.errors import TokenInvalidError, UserNotFoundError
from backend.core.repository.user_repository import UserRepository
from backend.core.repository.user_session_repository import UserSessionRepository
from backend.core.user import User
from backend.core.utils import normalize_email


@dataclass
class GetUserByTokenQuery:
    token: str


class GetUserByTokenQueryHandler:
    def __init__(
        self,
        access_token_service: AccessTokenGenerator,
        user_repository: UserRepository,
        user_session_repository: UserSessionRepository | None = None,
    ):
        self._access_token_service = access_token_service
        self._user_repository = user_repository
        self._user_session_repository = user_session_repository

    async def __call__(self, query: GetUserByTokenQuery) -> User:
        access_token = self._access_token_service.decode_access_token(query.token)
        access_token.validate()

        if access_token.session_id and self._user_session_repository is not None:
            session = await self._user_session_repository.get_by_id(
                access_token.session_id
            )
            if (
                session is None
                or session.revoked_at is not None
                or session.expires_at <= datetime.now(timezone.utc)
            ):
                raise TokenInvalidError("Session is revoked or expired")

        email = normalize_email(access_token.email)
        user = await self._user_repository.get_by_email(email)

        if user is None:
            raise UserNotFoundError()

        return user
