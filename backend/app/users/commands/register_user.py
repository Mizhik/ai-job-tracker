from dataclasses import dataclass
from datetime import timezone, datetime
from uuid import uuid4

from backend.core.abc.password_hasher import PasswordHasher
from backend.core.errors import UserAlreadyExistsException
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


@dataclass
class RegisterUserCommand:
    first_name: str
    last_name: str
    email: str
    password: str


class RegisterUserCommandHandler:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ):
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def handle(self, command: RegisterUserCommand) -> User:
        existing_user = await self._user_repository.get_by_email(command.email)
        if existing_user:
            raise UserAlreadyExistsException(
                f"User with email {command.email} already exists"
            )

        hashed_password = self._password_hasher.hash(command.password)

        new_user = User(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
            first_name=command.first_name,
            last_name=command.last_name,
            email=command.email,
            hashed_password=hashed_password,
        )

        await self._user_repository.create(new_user)
        return new_user
