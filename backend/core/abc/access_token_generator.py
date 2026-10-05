from abc import ABC, abstractmethod
from datetime import timedelta
from uuid import UUID

from backend.core.token import DecodedAccessToken


class AccessTokenGenerator(ABC):
    @abstractmethod
    def create_access_token(
        self,
        email: str,
        expires_delta: timedelta | None = None,
        session_id: UUID | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode_access_token(self, token: str) -> DecodedAccessToken:
        raise NotImplementedError
