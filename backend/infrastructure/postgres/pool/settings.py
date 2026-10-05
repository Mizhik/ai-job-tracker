import pydantic_settings


class DBSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="POSTGRES_", case_sensitive=False
    )

    dbname: str
    user: str
    password: str
    address: str

    def get_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.address}/{self.dbname}"
