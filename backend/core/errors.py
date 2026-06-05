from typing import ClassVar


class DomainException(Exception):
    default_detail: ClassVar[str]

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class UserAlreadyExistsException(DomainException):
    default_detail = "Email already in use"

class EmailOrPasswordIncorrectError(DomainException):
    default_detail = "Email or password is incorrect"

class UserBlockedError(DomainException):
    default_detail = "User is blocked"

class UserNotFoundError(DomainException):
    default_detail = "User not found"

class TokenIsExpiredError(DomainException):
    default_detail = "Token is expired"

class TokenInvalidError(DomainException):
    default_detail = "Token is invalid"