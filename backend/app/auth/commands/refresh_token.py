from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.session_token_service import SessionTokenService
from backend.core.errors import TokenInvalidError, UserBlockedError, UserNotFoundError
from backend.core.repository.user_repository import UserRepository
from backend.core.repository.user_session_repository import UserSessionRepository


@dataclass
class RefreshTokenCommand:
    raw_refresh_token: str
    csrf_token: str
    secret_key: str


@dataclass
class RefreshResult:
    access_token: str
    raw_refresh_token: str


class RefreshTokenCommandHandler:
    def __init__(
        self,
        user_session_repository: UserSessionRepository,
        user_repository: UserRepository,
        access_token_generator: AccessTokenGenerator,
        session_token_service: SessionTokenService,
        access_token_expire_delta: timedelta | None = None,
    ):
        self._user_session_repository = user_session_repository
        self._user_repository = user_repository
        self._access_token_generator = access_token_generator
        self._session_token_service = session_token_service
        self._access_token_expire_delta = access_token_expire_delta

    async def __call__(self, command: RefreshTokenCommand) -> RefreshResult:
        if not command.raw_refresh_token:
            raise TokenInvalidError("Missing refresh token")

        try:
            session_id, _ = self._session_token_service.parse_refresh_token(
                command.raw_refresh_token
            )
        except ValueError:
            raise TokenInvalidError("Invalid refresh token format")

        if not self._session_token_service.verify_csrf_token(
            session_id=session_id,
            secret_key=command.secret_key,
            csrf_token=command.csrf_token,
        ):
            raise TokenInvalidError("Invalid CSRF token")

        old_refresh_token_hash = self._session_token_service.hash_token(
            command.raw_refresh_token
        )
        new_raw_refresh_token, new_refresh_token_hash = (
            self._session_token_service.generate_refresh_token(session_id)
        )

        updated_session = await self._user_session_repository.rotate_refresh_token(
            session_id=session_id,
            old_refresh_token_hash=old_refresh_token_hash,
            new_refresh_token_hash=new_refresh_token_hash,
        )

        if updated_session is None:
            # Atomic swap failed (stale token, expired, or revoked session).
            raise TokenInvalidError("Invalid or expired refresh token")

        if (
            updated_session.revoked_at is not None
            or updated_session.expires_at <= datetime.now(timezone.utc)
        ):
            raise TokenInvalidError("Session is revoked or expired")

        user = await self._user_repository.get_by_id(updated_session.user_id)
        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserBlockedError()

        access_token = self._access_token_generator.create_access_token(
            email=user.email,
            expires_delta=self._access_token_expire_delta,
            session_id=updated_session.id,
        )

        return RefreshResult(
            access_token=access_token,
            raw_refresh_token=new_raw_refresh_token,
        )
