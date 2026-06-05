from dataclasses import dataclass

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.abc.password_hasher import PasswordHasher
from backend.core.errors import EmailOrPasswordIncorrectError
from backend.core.repository.user_repository import UserRepository
from backend.infrastructure.settings.auth import AuthSettings


@dataclass
class LoginCommand:
    email: str
    password: str


class LoginCommandHandler:

    def __init__(
        self,
        access_token_generator: AccessTokenGenerator,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        settings: AuthSettings,
    ):
        self._access_token_generator = access_token_generator
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._settings = settings

    async def __call__(self, command: LoginCommand) -> str:
        user = await self._user_repository.get_by_email(command.email)

        if not user:
            raise EmailOrPasswordIncorrectError()

        user.login(command.password, self._password_hasher.verify)

        return self._create_access_token(user.email)

    def _create_access_token(self, email: str) -> str:
        return self._access_token_generator.create_access_token(
            email=email,
            expires_delta=self._settings.access_token_expire_delta,
        )
