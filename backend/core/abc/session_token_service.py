from abc import ABC, abstractmethod
from uuid import UUID


class SessionTokenService(ABC):
    @abstractmethod
    def generate_refresh_token(self, session_id: UUID) -> tuple[str, str]:
        raise NotImplementedError

    @abstractmethod
    def hash_token(self, token: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_refresh_token(self, raw_token: str) -> tuple[UUID, str]:
        raise NotImplementedError

    @abstractmethod
    def generate_csrf_token(self, session_id: UUID, secret_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify_csrf_token(
        self, session_id: UUID, secret_key: str, csrf_token: str
    ) -> bool:
        raise NotImplementedError
