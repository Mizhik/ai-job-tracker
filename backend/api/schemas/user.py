from typing import Self
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from backend.app.users.commands.register_user import RegisterUserCommand
from backend.app.users.commands.update_user import UpdateUserCommand
from backend.core.user import User


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        validate_value = value.strip()
        if validate_value is None:
            raise ValueError("Password is required")

        if len(validate_value) < 8:
            raise ValueError("Password must be at least 8 characters long")

        return validate_value

    def to_command(self) -> RegisterUserCommand:
        return RegisterUserCommand(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            password=self.password,
        )


class UserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None

    @field_validator("email")
    def validate_email(cls, value: EmailStr | None) -> EmailStr | None:
        if value is not None and not value.strip():
            raise ValueError("Email cannot be empty")

        return value

    @field_validator("first_name")
    def validate_first_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("First name cannot be empty")

        if value is not None and len(value.strip()) < 2:
            raise ValueError("First name must be at least 2 characters long")
        return value

    @field_validator("last_name")
    def validate_last_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Last name cannot be empty")

        if value is not None and len(value.strip()) < 2:
            raise ValueError("Last name must be at least 2 characters long")
        return value

    def to_command(self, user_id: UUID, current_user: User) -> UpdateUserCommand:
        return UpdateUserCommand(
            id=user_id,
            current_user=current_user,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
        )

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None

    @classmethod
    def from_user(cls, user: User) -> Self:
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
