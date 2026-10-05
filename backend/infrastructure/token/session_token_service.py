import hashlib
import hmac
import secrets
from uuid import UUID

from backend.core.abc.session_token_service import SessionTokenService


class DefaultSessionTokenService(SessionTokenService):
    def hash_token(self, token: str) -> str:
        """Computes SHA-256 hash of a plain token string."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def generate_refresh_token(self, session_id: UUID) -> tuple[str, str]:
        """Generates a tuple of (raw_refresh_token, hashed_refresh_token).
        Format of raw refresh token: <session_id>.<random_secret>
        """
        secret = secrets.token_urlsafe(32)
        raw_token = f"{session_id}.{secret}"
        hashed = self.hash_token(raw_token)
        return raw_token, hashed

    def parse_refresh_token(self, raw_token: str) -> tuple[UUID, str]:
        """Parses raw refresh token into (session_id, raw_token).
        Raises ValueError if raw token format is invalid.
        """
        parts = raw_token.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid refresh token format")
        session_id = UUID(parts[0])
        return session_id, raw_token

    def generate_csrf_token(self, session_id: UUID, secret_key: str) -> str:
        """Generates a deterministic domain-separated HMAC CSRF token bound to session_id."""
        message = f"csrf:{session_id}".encode("utf-8")
        key = secret_key.encode("utf-8")
        return hmac.new(key, message, hashlib.sha256).hexdigest()

    def verify_csrf_token(
        self, session_id: UUID, secret_key: str, csrf_token: str
    ) -> bool:
        """Verifies candidate CSRF token against expected HMAC CSRF token using constant-time comparison."""
        if not csrf_token:
            return False
        expected = self.generate_csrf_token(session_id, secret_key)
        return hmac.compare_digest(expected, csrf_token)
