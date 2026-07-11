from pydantic import BaseModel, EmailStr

from backend.app.auth.commands.login import LoginCommand


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    def to_command(self) -> LoginCommand:
        return LoginCommand(
            email=self.email,
            password=self.password,
        )
