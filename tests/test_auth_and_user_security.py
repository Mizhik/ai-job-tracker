from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from backend.api.dependencies import ActiveUserDependency, CurrentUserDependency, oauth2_scheme
from backend.api.endpoints.get_user_by_token import get_user_by_token
from backend.api.endpoints.jobs.list_jobs import list_jobs
from backend.api.endpoints.login import login_for_access_token
from backend.app.auth.commands.login import LoginCommandHandler
from backend.app.auth.queries.get_user_by_token import GetUserByTokenQuery
from backend.app.auth.service import AuthService
from backend.app.users.commands.update_user import UpdateUserCommand, UpdateUserCommandHandler
from backend.core.errors import (
    EmailOrPasswordIncorrectError,
    NoUpdateDataProvidedError,
    TokenInvalidError,
    TokenIsExpiredError,
    UserBlockedError,
)
from backend.core.user import User
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService


class MockUserRepository:
    def __init__(self, users=None):
        self.users = users or {}

    async def get_by_email(self, email: str):
        return self.users.get(email)

    async def get_by_id(self, user_id):
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

    async def update(self, user):
        self.users[user.email] = user


@pytest.fixture
def auth_settings():
    return AuthSettings(
        secret_key="test-secret-key-for-jwt-service",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )


@pytest.fixture
def jwt_service(auth_settings):
    return JwtTokenService(settings=auth_settings)


# --- Unit Tests ---

def test_jwt_token_service_decode_valid(jwt_service):
    token = jwt_service.create_access_token(email="user@example.com")
    decoded = jwt_service.decode_access_token(token)
    assert decoded.email == "user@example.com"
    assert not decoded.is_expired


def test_jwt_token_service_decode_missing_sub(jwt_service, auth_settings):
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(payload, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    with pytest.raises(TokenInvalidError, match="missing subject"):
        jwt_service.decode_access_token(token)


def test_jwt_token_service_decode_missing_exp(jwt_service, auth_settings):
    payload = {"sub": "user@example.com"}
    token = jwt.encode(payload, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    with pytest.raises(TokenInvalidError, match="missing expiration"):
        jwt_service.decode_access_token(token)


def test_jwt_token_service_decode_malformed_exp(jwt_service, auth_settings):
    payload = {"sub": "user@example.com", "exp": "not-a-timestamp"}
    token = jwt.encode(payload, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    with pytest.raises(TokenInvalidError):
        jwt_service.decode_access_token(token)


def test_jwt_token_service_decode_invalid_email_format(jwt_service, auth_settings):
    payload = {"sub": "not-an-email", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(payload, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    with pytest.raises(TokenInvalidError):
        jwt_service.decode_access_token(token)


def test_jwt_token_service_decode_expired(jwt_service, auth_settings):
    payload = {
        "sub": "user@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    token = jwt.encode(payload, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    with pytest.raises(TokenIsExpiredError):
        jwt_service.decode_access_token(token)


def test_jwt_token_service_decode_bad_signature(jwt_service):
    payload = {"sub": "user@example.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    with pytest.raises(TokenInvalidError):
        jwt_service.decode_access_token(token)


@pytest.mark.asyncio
async def test_update_user_command_handler_no_data():
    user_repo = MockUserRepository()
    handler = UpdateUserCommandHandler(user_repository=user_repo)
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        first_name="First",
        last_name="Last",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    cmd = UpdateUserCommand(id=user.id, current_user=user)
    with pytest.raises(NoUpdateDataProvidedError):
        await handler.handle(cmd)


# --- HTTP API Boundary / TestClient Integration Tests ---

class MockContainer:
    def __init__(self, auth_service):
        self._auth_service = auth_service
        self._get_current_user = CurrentUserDependency(
            auth_service=auth_service,
            oauth2_scheme=oauth2_scheme,
        )
        self._require_active_user = ActiveUserDependency(
            get_current_user=self._get_current_user
        )

    async def get_current_user(self):
        return self._get_current_user

    async def require_active_user(self):
        return self._require_active_user


from backend.api.endpoints.jobs import router as jobs_router


@pytest.fixture
def test_app_and_repo(jwt_service, auth_settings):
    hasher = Argon2PasswordHasher()
    hashed_password = hasher.hash("password123")

    active_user = User(
        id=uuid4(),
        email="active@example.com",
        hashed_password=hashed_password,
        first_name="Active",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    inactive_user = User(
        id=uuid4(),
        email="inactive@example.com",
        hashed_password=hashed_password,
        first_name="Inactive",
        last_name="User",
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )

    repo = MockUserRepository(
        users={
            "active@example.com": active_user,
            "inactive@example.com": inactive_user,
        }
    )

    auth_service = AuthService(
        user_repository=repo,
        password_hasher=hasher,
        access_token_generator=jwt_service,
        access_token_expire_delta=auth_settings.access_token_expire_delta,
    )

    app = FastAPI()
    app.state.container = MockContainer(auth_service=auth_service)

    app.add_api_route("/users/me", get_user_by_token, methods=["GET"])
    app.include_router(jobs_router)

    return app, repo, jwt_service, auth_settings


def test_missing_bearer_token_returns_401(test_app_and_repo):
    app, _, _, _ = test_app_and_repo
    client = TestClient(app)

    res_me = client.get("/users/me")
    assert res_me.status_code == 401
    assert res_me.headers.get("WWW-Authenticate") == "Bearer"

    res_jobs = client.get("/jobs")
    assert res_jobs.status_code == 401
    assert res_jobs.headers.get("WWW-Authenticate") == "Bearer"


def test_malformed_token_returns_401(test_app_and_repo):
    app, _, _, _ = test_app_and_repo
    client = TestClient(app)

    headers = {"Authorization": "Bearer not-a-valid-jwt"}
    res = client.get("/users/me", headers=headers)
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_token_missing_subject_returns_401(test_app_and_repo):
    app, _, _, auth_settings = test_app_and_repo
    client = TestClient(app)

    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_token_invalid_email_claim_returns_401(test_app_and_repo):
    app, _, _, auth_settings = test_app_and_repo
    client = TestClient(app)

    token = jwt.encode(
        {
            "sub": "not-an-email",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_token_malformed_exp_returns_401(test_app_and_repo):
    app, _, _, auth_settings = test_app_and_repo
    client = TestClient(app)

    token = jwt.encode(
        {"sub": "active@example.com", "exp": "invalid_exp"},
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_expired_token_returns_401(test_app_and_repo):
    app, _, _, auth_settings = test_app_and_repo
    client = TestClient(app)

    token = jwt.encode(
        {
            "sub": "active@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_token_deleted_user_returns_401(test_app_and_repo):
    app, _, jwt_service, _ = test_app_and_repo
    client = TestClient(app)

    token = jwt_service.create_access_token(email="nonexistent@example.com")
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_inactive_user_returns_403(test_app_and_repo):
    app, _, jwt_service, _ = test_app_and_repo
    client = TestClient(app)

    token = jwt_service.create_access_token(email="inactive@example.com")

    res_me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 403
    assert res_me.json()["detail"] == "User is not active"

    res_jobs = client.get("/jobs", headers={"Authorization": f"Bearer {token}"})
    assert res_jobs.status_code == 403
    assert res_jobs.json()["detail"] == "User is not active"


def test_active_user_returns_200(test_app_and_repo):
    app, _, jwt_service, _ = test_app_and_repo
    client = TestClient(app)

    token = jwt_service.create_access_token(email="active@example.com")
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "active@example.com"


@pytest.mark.asyncio
async def test_login_and_error_handling(test_app_and_repo):
    app, repo, jwt_service, auth_settings = test_app_and_repo
    hasher = Argon2PasswordHasher()

    # LoginCommandHandler with wrong password -> EmailOrPasswordIncorrectError
    handler = LoginCommandHandler(
        access_token_generator=jwt_service,
        user_repository=repo,
        password_hasher=hasher,
        expires_delta=auth_settings.access_token_expire_delta,
    )

    from backend.app.auth.commands.login import LoginCommand
    with pytest.raises(EmailOrPasswordIncorrectError):
        await handler(LoginCommand(email="active@example.com", password="wrongpassword"))

    # LoginCommandHandler with blocked user -> UserBlockedError
    blocked_user = User(
        id=uuid4(),
        email="blocked@example.com",
        hashed_password=hasher.hash("password123"),
        first_name="Blocked",
        last_name="User",
        is_active=False,
        is_blocked=True,
        created_at=datetime.now(timezone.utc),
    )
    repo.users["blocked@example.com"] = blocked_user

    with pytest.raises(UserBlockedError):
        await handler(LoginCommand(email="blocked@example.com", password="password123"))
