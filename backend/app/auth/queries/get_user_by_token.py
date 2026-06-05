from dataclasses import dataclass

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.errors import UserNotFoundError
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


@dataclass
class GetUserByTokenQuery:
    token: str


class GetUserByTokenQueryHandler:
    def __init__(
        self,
        access_token_service: AccessTokenGenerator,
        user_repository: UserRepository,
    ):
        self._access_token_service = access_token_service
        self._user_repository = user_repository

    async def __call__(self, query: GetUserByTokenQuery) -> User:
        access_token = self._access_token_service.decode_access_token(query.token)
        access_token.validate()

        user = await self._user_repository.get_by_email(access_token.email)

        if user is None:
            raise UserNotFoundError()

        return user
