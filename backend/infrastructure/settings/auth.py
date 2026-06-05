import datetime
import pydantic_settings


class AuthSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="AUTH_", case_sensitive=False
    )
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    @property
    def access_token_expire_delta(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=self.access_token_expire_minutes)
