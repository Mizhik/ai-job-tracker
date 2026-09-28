import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramAdminSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = ""
    telegram_admin_user_id: int = 0
    api_base_url: str = "http://app:8000"

    # Database settings fallback
    postgres_dbname: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_address: str = "localhost:5432"

    def get_postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_address}/{self.postgres_dbname}"


def load_settings() -> TelegramAdminSettings:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "")
    admin_id_str = os.getenv("TELEGRAM_ADMIN_USER_ID") or os.getenv("TELEGRAM_ALLOWED_USER_ID", "0")
    try:
        admin_id = int(admin_id_str)
    except ValueError:
        admin_id = 0

    api_url = os.getenv("API_BASE_URL", "http://app:8000")
    postgres_dbname = os.getenv("POSTGRES_DBNAME", "postgres")
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_address = os.getenv("POSTGRES_ADDRESS", "localhost:5432")

    return TelegramAdminSettings(
        telegram_bot_token=token,
        telegram_admin_user_id=admin_id,
        api_base_url=api_url,
        postgres_dbname=postgres_dbname,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_address=postgres_address,
    )
