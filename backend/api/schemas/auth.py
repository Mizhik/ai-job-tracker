from pydantic import BaseModel, EmailStr, field_validator

from backend.app.auth.commands.login import LoginCommand
from backend.core.utils import normalize_email


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="after")
    def normalize_email_field(cls, value: EmailStr) -> str:
        return normalize_email(value)

    def to_command(self) -> LoginCommand:
        return LoginCommand(
            email=self.email,
            password=self.password,
        )
