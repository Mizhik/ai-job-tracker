from dataclasses import dataclass
from datetime import timedelta

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.errors import EmailOrPasswordIncorrectError
from backend.core.repository.user_repository import UserRepository
from backend.core.utils import normalize_email


@dataclass
class LoginCommand:
    email: str
    password: str

    def __post_init__(self):
        self.email = normalize_email(self.email)


class LoginCommandHandler:

    def __init__(
        self,
        access_token_generator: AccessTokenGenerator,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        expires_delta: timedelta | None = None,
    ):
        self._access_token_generator = access_token_generator
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._expires_delta = expires_delta

    async def __call__(self, command: LoginCommand) -> str:
        user = await self._user_repository.get_by_email(command.email)

        if not user:
            raise EmailOrPasswordIncorrectError()

        user.login(command.password, self._password_hasher.verify)

        return self._create_access_token(user.email)

    def _create_access_token(self, email: str) -> str:
        return self._access_token_generator.create_access_token(
            email=email,
            expires_delta=self._expires_delta,
        )
