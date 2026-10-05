from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.container import Container
from backend.api.endpoints import router as user_router
from backend.app.auth.service import AuthService
from backend.core.repository.user_session_repository import UserSessionRepository
from backend.core.session import UserSession
from backend.core.user import User
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService
from backend.infrastructure.token.session_token_service import DefaultSessionTokenService


class InMemoryUserSessionRepository(UserSessionRepository):
    def __init__(self):
        self.sessions: dict[UUID, UserSession] = {}

    async def create(self, session: UserSession) -> None:
        self.sessions[session.id] = session

    async def get_by_id(self, session_id: UUID) -> UserSession | None:
        return self.sessions.get(session_id)

    async def rotate_refresh_token(
        self,
        session_id: UUID,
        old_refresh_token_hash: str,
        new_refresh_token_hash: str,
    ) -> UserSession | None:
        session = self.sessions.get(session_id)
        if not session:
            return None
        now = datetime.now(timezone.utc)
        if session.revoked_at is not None or session.expires_at <= now:
            return None
        if session.refresh_token_hash != old_refresh_token_hash:
            return None

        session.refresh_token_hash = new_refresh_token_hash
        session.updated_at = now
        return session

    async def revoke(self, session_id: UUID) -> None:
        session = self.sessions.get(session_id)
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            session.updated_at = datetime.now(timezone.utc)


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

    async def create(self, user: User) -> None:
        self.users[user.email] = user

    async def update(self, user: User) -> None:
        self.users[user.email] = user


@pytest.fixture
def session_test_app():
    settings = AuthSettings(
        secret_key="session-test-secret-key-32-chars-minimum",
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_cookie_name="refresh_token",
        cookie_secure=False,
        allowed_origins=["http://localhost", "http://localhost:3000"],
    )
    jwt_service = JwtTokenService(settings=settings)
    session_token_service = DefaultSessionTokenService()
    hasher = Argon2PasswordHasher()
    hashed_pass = hasher.hash("password123")

    user_id = uuid4()
    active_user = User(
        id=user_id,
        email="user@example.com",
        hashed_password=hashed_pass,
        first_name="Session",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    user_repo = MockUserRepository({"user@example.com": active_user})
    session_repo = InMemoryUserSessionRepository()

    auth_service = AuthService(
        user_repository=user_repo,
        password_hasher=hasher,
        access_token_generator=jwt_service,
        user_session_repository=session_repo,
        session_token_service=session_token_service,
        access_token_expire_delta=settings.access_token_expire_delta,
    )

    container = Container()
    container.auth_settings.override(settings)
    container.user_repository.override(user_repo)
    container.user_session_repository.override(session_repo)
    container.session_token_service.override(session_token_service)
    container.auth_service.override(auth_service)
    container.wire(packages=["backend.api"])

    app = FastAPI()
    app.state.container = container
    app.include_router(user_router)

    client = TestClient(app)

    yield client, auth_service, user_repo, session_repo, settings, active_user, jwt_service

    container.unwire()


def test_login_creates_session_and_sets_cookie(session_test_app):
    client, _, _, session_repo, settings, active_user, _ = session_test_app

    res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Check HttpOnly cookie
    assert settings.refresh_cookie_name in res.cookies

    # Verify session recorded in repo with 7-day expiration
    assert len(session_repo.sessions) == 1
    session = list(session_repo.sessions.values())[0]
    assert session.user_id == active_user.id
    assert session.revoked_at is None
    assert session.expires_at > datetime.now(timezone.utc) + timedelta(days=6)


def test_get_csrf_token_no_origin_required(session_test_app):
    client, _, _, session_repo, settings, active_user, _ = session_test_app

    # Login to get cookie
    login_res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    cookie_val = login_res.cookies[settings.refresh_cookie_name]

    # GET /users/csrf with cookie, no Origin header
    csrf_res = client.get("/users/csrf", cookies={settings.refresh_cookie_name: cookie_val})
    assert csrf_res.status_code == 200
    csrf_data = csrf_res.json()
    assert "csrf_token" in csrf_data
    assert len(csrf_data["csrf_token"]) > 10


def test_refresh_token_rotation_and_stale_cookie_protection(session_test_app):
    client, _, _, session_repo, settings, active_user, _ = session_test_app

    # Login
    login_res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    old_cookie = login_res.cookies[settings.refresh_cookie_name]

    # Get CSRF
    csrf_res = client.get("/users/csrf", cookies={settings.refresh_cookie_name: old_cookie})
    csrf_token = csrf_res.json()["csrf_token"]

    # Refresh token with valid Origin and CSRF
    refresh_res = client.post(
        "/users/refresh",
        cookies={settings.refresh_cookie_name: old_cookie},
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    new_cookie = refresh_res.cookies[settings.refresh_cookie_name]
    assert new_cookie != old_cookie

    # Old cookie cannot fetch CSRF token anymore -> 401
    stale_csrf_res = client.get("/users/csrf", cookies={settings.refresh_cookie_name: old_cookie})
    assert stale_csrf_res.status_code == 401
    assert "Invalid or stale refresh token" in stale_csrf_res.json()["detail"]

    # Old cookie cannot logout or revoke current active session -> 401
    stale_logout_res = client.post(
        "/users/logout",
        cookies={settings.refresh_cookie_name: old_cookie},
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf_token},
    )
    assert stale_logout_res.status_code == 401
    assert "Invalid or stale refresh token" in stale_logout_res.json()["detail"]

    # Session remains active in DB
    session_id = list(session_repo.sessions.keys())[0]
    session = session_repo.sessions[session_id]
    assert session.revoked_at is None

    # Test 7-day absolute cutoff: expire session
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    # Refresh on expired session fails with 401
    csrf_res2 = client.get("/users/csrf", cookies={settings.refresh_cookie_name: new_cookie})
    assert csrf_res2.status_code == 401


def test_origin_and_referer_enforcement_on_refresh_and_logout(session_test_app):
    client, _, _, _, settings, _, _ = session_test_app

    login_res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    cookie_val = login_res.cookies[settings.refresh_cookie_name]
    csrf_res = client.get("/users/csrf", cookies={settings.refresh_cookie_name: cookie_val})
    csrf_token = csrf_res.json()["csrf_token"]

    # Missing Origin & Referer -> 403 Forbidden
    res_no_origin = client.post(
        "/users/refresh",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_no_origin.status_code == 403
    assert "Missing Origin and Referer" in res_no_origin.json()["detail"]

    # Unauthorized Origin -> 403 Forbidden
    res_bad_origin = client.post(
        "/users/refresh",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"Origin": "http://evil-attacker.com", "X-CSRF-Token": csrf_token},
    )
    assert res_bad_origin.status_code == 403
    assert "Origin not allowed" in res_bad_origin.json()["detail"]

    # Valid Referer -> 200 OK
    res_valid_referer = client.post(
        "/users/refresh",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"Referer": "http://localhost:3000/dashboard", "X-CSRF-Token": csrf_token},
    )
    assert res_valid_referer.status_code == 200


def test_logout_csrf_header_validation_regression(session_test_app):
    client, _, _, session_repo, settings, _, _ = session_test_app

    # Login
    login_res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    cookie_val = login_res.cookies[settings.refresh_cookie_name]

    # 1. Cookie present, X-CSRF-Token header missing -> 401 Unauthorized
    logout_no_csrf = client.post(
        "/users/logout",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"Origin": "http://localhost:3000"},
    )
    assert logout_no_csrf.status_code == 401
    assert "Missing CSRF token" in logout_no_csrf.json()["detail"]

    # Verify session was NOT revoked
    session_id = list(session_repo.sessions.keys())[0]
    assert session_repo.sessions[session_id].revoked_at is None

    # 2. Cookie present, X-CSRF-Token header invalid -> 401 Unauthorized
    logout_invalid_csrf = client.post(
        "/users/logout",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": "invalid-csrf-token"},
    )
    assert logout_invalid_csrf.status_code == 401
    assert "Invalid CSRF token" in logout_invalid_csrf.json()["detail"]

    # Verify session was NOT revoked
    assert session_repo.sessions[session_id].revoked_at is None


def test_logout_revokes_session_and_invalidates_access_token(session_test_app):
    client, _, _, session_repo, settings, _, _ = session_test_app

    # Login
    login_res = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    access_token = login_res.json()["access_token"]
    cookie_val = login_res.cookies[settings.refresh_cookie_name]

    # Verify access token works on GET /users/me
    me_res = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "user@example.com"

    # Get CSRF
    csrf_res = client.get("/users/csrf", cookies={settings.refresh_cookie_name: cookie_val})
    csrf_token = csrf_res.json()["csrf_token"]

    # Logout
    logout_res = client.post(
        "/users/logout",
        cookies={settings.refresh_cookie_name: cookie_val},
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf_token},
    )
    assert logout_res.status_code == 200

    # Cookie is deleted
    assert settings.refresh_cookie_name not in logout_res.cookies or logout_res.cookies[settings.refresh_cookie_name] == ""

    # Session is revoked in DB
    session_id = list(session_repo.sessions.keys())[0]
    assert session_repo.sessions[session_id].revoked_at is not None

    # Access token fails immediately on GET /users/me
    me_after_logout = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["detail"] in ("Token is invalid", "Session is revoked or expired")
