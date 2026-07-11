import datetime

from jose import jwt

from backend.core.abc.access_token_generator import AccessTokenGenerator
from backend.core.token import DecodedAccessToken
from backend.infrastructure.settings.auth import AuthSettings


class JwtTokenService(AccessTokenGenerator):
    _EXPIRATION_MINUTES = 15

    def __init__(self, settings: AuthSettings):
        self._settings = settings

    def create_access_token(
        self,
        email: str,
        expires_delta: datetime.timedelta | None = None,
    ) -> str:
        to_encode = {
            "sub": str(email),
        }

        if expires_delta:
            expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
        else:
            expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                minutes=self._EXPIRATION_MINUTES
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            self._settings.secret_key,
            algorithm=self._settings.algorithm,
        )

        return encoded_jwt

    def decode_access_token(self, token: str) -> DecodedAccessToken:
        payload = jwt.decode(
            token,
            self._settings.secret_key,
            algorithms=[self._settings.algorithm],
        )
        email = payload.get("sub")
        if not email:
            raise ValueError("Invalid token: missing subject")

        expires_at = datetime.datetime.fromtimestamp(
            payload.get("exp"), tz=datetime.timezone.utc
        )

        return DecodedAccessToken(email=email, expires_at=expires_at)
