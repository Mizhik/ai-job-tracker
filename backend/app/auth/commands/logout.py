from dataclasses import dataclass
from datetime import datetime, timezone

from backend.core.abc.session_token_service import SessionTokenService
from backend.core.errors import TokenInvalidError
from backend.core.repository.user_session_repository import UserSessionRepository


@dataclass
class LogoutCommand:
    raw_refresh_token: str
    csrf_token: str
    secret_key: str


class LogoutCommandHandler:
    def __init__(
        self,
        user_session_repository: UserSessionRepository,
        session_token_service: SessionTokenService,
    ):
        self._user_session_repository = user_session_repository
        self._session_token_service = session_token_service

    async def __call__(self, command: LogoutCommand) -> None:
        if not command.raw_refresh_token:
            return

        try:
            session_id, _ = self._session_token_service.parse_refresh_token(
                command.raw_refresh_token
            )
        except ValueError:
            raise TokenInvalidError("Invalid refresh token format")

        session = await self._user_session_repository.get_by_id(session_id)
        if (
            session is None
            or session.revoked_at is not None
            or session.expires_at <= datetime.now(timezone.utc)
        ):
            raise TokenInvalidError("Session is revoked or expired")

        token_hash = self._session_token_service.hash_token(command.raw_refresh_token)
        if session.refresh_token_hash != token_hash:
            raise TokenInvalidError("Invalid or stale refresh token")

        if not self._session_token_service.verify_csrf_token(
            session_id=session_id,
            secret_key=command.secret_key,
            csrf_token=command.csrf_token,
        ):
            raise TokenInvalidError("Invalid CSRF token")

        await self._user_session_repository.revoke(session_id)
