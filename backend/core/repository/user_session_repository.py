from abc import ABC, abstractmethod
from uuid import UUID

from backend.core.session import UserSession


class UserSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: UserSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> UserSession | None:
        raise NotImplementedError

    @abstractmethod
    async def rotate_refresh_token(
        self,
        session_id: UUID,
        old_refresh_token_hash: str,
        new_refresh_token_hash: str,
    ) -> UserSession | None:
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, session_id: UUID) -> None:
        raise NotImplementedError
