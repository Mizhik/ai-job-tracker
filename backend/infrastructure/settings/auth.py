import datetime
from pydantic import field_validator
import pydantic_settings


class AuthSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="AUTH_", case_sensitive=False
    )
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = True
    cookie_samesite: str = "lax"
    allowed_origins: list[str] | str = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def access_token_expire_delta(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=self.access_token_expire_minutes)
