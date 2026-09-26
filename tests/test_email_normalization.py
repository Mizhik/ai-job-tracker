from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from backend.api.endpoints.login import login_for_access_token
from backend.api.endpoints.register_user import register_user
from backend.api.endpoints.update_user import update_user
from backend.api.schemas.auth import LoginRequest
from backend.api.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest
from backend.app.auth.commands.login import LoginCommand, LoginCommandHandler
from backend.app.users.commands.register_user import RegisterUserCommand, RegisterUserCommandHandler
from backend.app.users.commands.update_user import UpdateUserCommand, UpdateUserCommandHandler
from backend.core.errors import EmailOrPasswordIncorrectError, UserAlreadyExistsException, UserBlockedError
from backend.core.user import User
from backend.core.utils import normalize_email
from backend.infrastructure.settings.auth import AuthSettings


class DummyUserRepository:
    def __init__(self):
        self.users_by_email = {}
        self.users_by_id = {}

    async def create(self, user: User) -> None:
        if user.email in self.users_by_email:
            raise UserAlreadyExistsException()
        self.users_by_email[user.email] = user
        self.users_by_id[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        return self.users_by_email.get(email)

    async def get_by_id(self, user_id) -> User | None:
        return self.users_by_id.get(user_id)

    async def update(self, user: User) -> None:
        for uid, u in self.users_by_email.items():
            if u.email == user.email and u.id != user.id:
                raise UserAlreadyExistsException()
        self.users_by_email[user.email] = user
        self.users_by_id[user.id] = user


class DummyPasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return f"hashed_{password}" == hashed


class DummyAccessTokenGenerator:
    def create_access_token(self, email: str, expires_delta=None) -> str:
        return f"token_for_{email}"


class DummyAuthService:
    def __init__(self, login_handler: LoginCommandHandler):
        self._login_handler = login_handler

    async def login(self, command: LoginCommand) -> str:
        return await self._login_handler(command)


class DummyUserService:
    def __init__(self, register_handler: RegisterUserCommandHandler, update_handler: UpdateUserCommandHandler):
        self._register_handler = register_handler
        self._update_handler = update_handler

    async def register_user(self, command: RegisterUserCommand) -> User:
        return await self._register_handler.handle(command)

    async def update_user(self, command: UpdateUserCommand) -> User:
        return await self._update_handler.handle(command)


def test_normalize_email_helper():
    assert normalize_email("  User@Example.COM ") == "user@example.com"
    assert normalize_email("FOO.bar@DOMAIN.org") == "foo.bar@domain.org"


def test_schemas_normalize_email():
    req = UserCreateRequest(
        first_name="John",
        last_name="Doe",
        email="  John.Doe@EXAMPLE.Com  ",
        password="password123",
    )
    assert req.email == "john.doe@example.com"

    login_req = LoginRequest(
        email=" USER@domain.com  ",
        password="password123",
    )
    assert login_req.email == "user@domain.com"

    update_req = UserUpdateRequest(
        email=" NewEmail@domain.COM "
    )
    assert update_req.email == "newemail@domain.com"


def test_invalid_email_validation():
    with pytest.raises(ValidationError):
        UserCreateRequest(
            first_name="John",
            last_name="Doe",
            email="not-an-email",
            password="password123",
        )

    with pytest.raises(ValidationError):
        LoginRequest(
            email="invalid_email",
            password="password123",
        )


@pytest.mark.asyncio
async def test_register_duplicate_with_case_and_whitespace():
    repo = DummyUserRepository()
    hasher = DummyPasswordHasher()
    handler = RegisterUserCommandHandler(repo, hasher)

    cmd1 = RegisterUserCommand(
        first_name="Alice",
        last_name="Smith",
        email="  Alice.Smith@Example.COM  ",
        password="password123",
    )
    user1 = await handler.handle(cmd1)
    assert user1.email == "alice.smith@example.com"

    cmd2 = RegisterUserCommand(
        first_name="Alice",
        last_name="Smith",
        email="ALICE.SMITH@EXAMPLE.COM",
        password="password123",
    )
    with pytest.raises(UserAlreadyExistsException):
        await handler.handle(cmd2)


@pytest.mark.asyncio
async def test_login_outcomes_domain():
    repo = DummyUserRepository()
    hasher = DummyPasswordHasher()
    token_gen = DummyAccessTokenGenerator()
    settings = AuthSettings(
        secret_key="secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )

    register_handler = RegisterUserCommandHandler(repo, hasher)
    login_handler = LoginCommandHandler(token_gen, repo, hasher, settings.access_token_expire_delta)

    await register_handler.handle(
        RegisterUserCommand(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            password="secretpassword",
        )
    )

    # Successful login with case/whitespace variations
    token = await login_handler(
        LoginCommand(email="  BOB@EXAMPLE.COM ", password="secretpassword")
    )
    assert token == "token_for_bob@example.com"

    # Non-existent user
    with pytest.raises(EmailOrPasswordIncorrectError):
        await login_handler(
            LoginCommand(email="unknown@example.com", password="secretpassword")
        )

    # Wrong password
    with pytest.raises(EmailOrPasswordIncorrectError):
        await login_handler(
            LoginCommand(email="bob@example.com", password="wrongpassword")
        )

    # Blocked user
    user = await repo.get_by_email("bob@example.com")
    user.is_active = False

    with pytest.raises(UserBlockedError):
        await login_handler(
            LoginCommand(email="bob@example.com", password="secretpassword")
        )


@pytest.mark.asyncio
async def test_update_user_email_normalization():
    repo = DummyUserRepository()
    update_handler = UpdateUserCommandHandler(repo)

    user_id = uuid4()
    user = User(
        id=user_id,
        created_at=datetime.now(timezone.utc),
        email="original@example.com",
        hashed_password="hashed_pass",
        first_name="Jane",
        last_name="Doe",
    )
    await repo.create(user)

    cmd = UpdateUserCommand(
        id=user_id,
        current_user=user,
        email="  Updated.Email@EXAMPLE.Com  ",
    )
    updated = await update_handler.handle(cmd)
    assert updated.email == "updated.email@example.com"


@pytest.mark.asyncio
async def test_api_endpoint_responses():
    repo = DummyUserRepository()
    hasher = DummyPasswordHasher()
    token_gen = DummyAccessTokenGenerator()
    settings = AuthSettings(
        secret_key="secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )

    register_handler = RegisterUserCommandHandler(repo, hasher)
    login_handler = LoginCommandHandler(token_gen, repo, hasher, settings.access_token_expire_delta)
    update_handler = UpdateUserCommandHandler(repo)

    auth_service = DummyAuthService(login_handler)
    user_service = DummyUserService(register_handler, update_handler)

    # 1. Register user via endpoint
    create_req = UserCreateRequest(
        first_name="Endpoint",
        last_name="User",
        email="  Endpoint.User@Example.COM  ",
        password="password123",
    )
    res_user = await register_user(user_create_request=create_req, user_service=user_service)
    assert res_user.email == "endpoint.user@example.com"

    # 2. Duplicate registration via endpoint (varying case/whitespace) -> HTTP 400
    duplicate_req = UserCreateRequest(
        first_name="Endpoint",
        last_name="User",
        email="ENDPOINT.USER@EXAMPLE.COM",
        password="password123",
    )
    with pytest.raises(HTTPException) as exc_info_dup:
        await register_user(user_create_request=duplicate_req, user_service=user_service)
    assert exc_info_dup.value.status_code == 400
    assert "already exists" in exc_info_dup.value.detail

    # 3. Non-existent email login via endpoint -> HTTP 401 with identical body and WWW-Authenticate header
    form_unknown = OAuth2PasswordRequestForm(
        username="UNKNOWN@EXAMPLE.COM",
        password="password123",
        scope="",
    )
    with pytest.raises(HTTPException) as exc_info_unknown:
        await login_for_access_token(auth_service=auth_service, form_data=form_unknown)

    # 4. Wrong password login via endpoint -> HTTP 401 with identical body and WWW-Authenticate header
    form_wrong_pass = OAuth2PasswordRequestForm(
        username="endpoint.user@example.com",
        password="wrong_password",
        scope="",
    )
    with pytest.raises(HTTPException) as exc_info_wrong_pass:
        await login_for_access_token(auth_service=auth_service, form_data=form_wrong_pass)

    assert exc_info_unknown.value.status_code == 401
    assert exc_info_wrong_pass.value.status_code == 401
    assert exc_info_unknown.value.detail == exc_info_wrong_pass.value.detail == "Email or password is incorrect"
    assert exc_info_unknown.value.headers == exc_info_wrong_pass.value.headers == {"WWW-Authenticate": "Bearer"}

    # 5. Blocked user login via endpoint -> HTTP 403
    user = await repo.get_by_email("endpoint.user@example.com")
    user.is_active = False

    form_blocked = OAuth2PasswordRequestForm(
        username="ENDPOINT.USER@EXAMPLE.COM",
        password="password123",
        scope="",
    )
    with pytest.raises(HTTPException) as exc_info_blocked:
        await login_for_access_token(auth_service=auth_service, form_data=form_blocked)
    assert exc_info_blocked.value.status_code == 403
    assert exc_info_blocked.value.detail == "User is blocked"

    # 6. Update email via endpoint
    user.is_active = True
    update_req = UserUpdateRequest(email="  NEW.ENDPOINT.USER@EXAMPLE.COM  ")
    updated_res = await update_user(
        user_id=user.id,
        user_update_request=update_req,
        current_user=user,
        user_service=user_service,
    )
    assert updated_res.email == "new.endpoint.user@example.com"


def test_user_response_no_password():
    user = User(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        email="test@example.com",
        hashed_password="hashed_secret_password",
        first_name="Test",
        last_name="User",
    )
    res = UserResponse.from_user(user)
    data = res.model_dump()
    assert "hashed_password" not in data
    assert "password" not in data
    assert data["email"] == "test@example.com"
