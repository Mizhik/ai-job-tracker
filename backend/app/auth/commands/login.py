from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.abc.session_token_service import SessionTokenService
from backend.core.errors import EmailOrPasswordIncorrectError
from backend.core.repository.user_repository import UserRepository
from backend.core.repository.user_session_repository import UserSessionRepository
from backend.core.session import UserSession
from backend.core.utils import normalize_email


@dataclass
class LoginCommand:
    email: str
    password: str

    def __post_init__(self):
        self.email = normalize_email(self.email)


@dataclass
class LoginResult:
    access_token: str
    raw_refresh_token: str
    session_id: UUID


class LoginCommandHandler:

    def __init__(
        self,
        access_token_generator: AccessTokenGenerator,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        user_session_repository: UserSessionRepository,
        session_token_service: SessionTokenService,
        expires_delta: timedelta | None = None,
        session_expires_days: int = 7,
    ):
        self._access_token_generator = access_token_generator
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._user_session_repository = user_session_repository
        self._session_token_service = session_token_service
        self._expires_delta = expires_delta
        self._session_expires_days = session_expires_days

    async def __call__(self, command: LoginCommand) -> LoginResult:
        user = await self._user_repository.get_by_email(command.email)

        if not user:
            raise EmailOrPasswordIncorrectError()

        user.login(command.password, self._password_hasher.verify)

        session_id = uuid4()
        raw_refresh_token, hashed_refresh_token = (
            self._session_token_service.generate_refresh_token(session_id)
        )
        now = datetime.now(timezone.utc)
        session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=hashed_refresh_token,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=self._session_expires_days),
            revoked_at=None,
        )
        await self._user_session_repository.create(session)

        access_token = self._access_token_generator.create_access_token(
            email=user.email,
            expires_delta=self._expires_delta,
            session_id=session_id,
        )

        return LoginResult(
            access_token=access_token,
            raw_refresh_token=raw_refresh_token,
            session_id=session_id,
        )
