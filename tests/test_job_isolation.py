from __future__ import annotations
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.container import Container
from backend.api.endpoints.jobs import router as jobs_router
from backend.app.auth.service import AuthService
from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.commands.update_job import UpdateJobCommand
from backend.app.jobs.commands.delete_job import DeleteJobCommand
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.service import JobService
from backend.core.errors import InvalidJobDataError, JobNotFoundError
from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository
from backend.core.user import User
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.postgres.job_repository import AsyncpgJobRepository
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService


class InMemoryJobRepository(JobRepository):
    def __init__(self):
        self.jobs: list[Job] = []

    async def create(self, job: Job) -> None:
        self.jobs.append(job)

    async def get_by_id(self, job_id: UUID, user_id: UUID) -> Job | None:
        for job in self.jobs:
            if job.id == job_id and job.user_id == user_id:
                return job
        return None

    async def list_and_count(
        self,
        user_id: UUID,
        q: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        user_jobs = [j for j in self.jobs if j.user_id == user_id]
        if q and q.strip():
            term = q.strip().lower()
            filtered = [
                j for j in user_jobs
                if term in j.title.lower() or term in j.company.lower()
            ]
        else:
            filtered = user_jobs

        if status and status.strip():
            st_term = status.strip().lower()
            if st_term == "saved":
                filtered = [j for j in filtered if j.application is None]
            else:
                filtered = [
                    j for j in filtered
                    if j.application is not None and j.application.status == st_term
                ]

        filtered.sort(key=lambda j: (j.created_at, j.id), reverse=True)
        total = len(filtered)
        paged = filtered[offset : offset + limit]
        return paged, total

    async def update(self, job: Job) -> bool:
        for idx, existing in enumerate(self.jobs):
            if existing.id == job.id and existing.user_id == job.user_id:
                self.jobs[idx] = job
                return True
        return False

    async def delete(self, job_id: UUID, user_id: UUID) -> bool:
        for idx, existing in enumerate(self.jobs):
            if existing.id == job_id and existing.user_id == user_id:
                del self.jobs[idx]
                return True
        return False


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


# --- Core Domain Validation Tests ---

@pytest.mark.asyncio
async def test_job_validation_rules():
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. Blank title or company
    with pytest.raises(InvalidJobDataError, match="Title cannot be blank"):
        Job(id=uuid4(), user_id=user_id, title="   ", company="Acme", created_at=now).validate()

    with pytest.raises(InvalidJobDataError, match="Company cannot be blank"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="", created_at=now).validate()

    # 2. Negative salary
    with pytest.raises(InvalidJobDataError, match="salary_min cannot be negative"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=-10, currency="USD", salary_period="year", created_at=now).validate()

    # 3. Min > Max salary
    with pytest.raises(InvalidJobDataError, match="salary_min cannot be greater than salary_max"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=100, salary_max=50, currency="USD", salary_period="year", created_at=now).validate()

    # 4. Numeric salary missing currency/period
    with pytest.raises(InvalidJobDataError, match="Numeric salary requires both currency and salary_period"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, created_at=now).validate()

    # 5. Invalid currency code
    with pytest.raises(InvalidJobDataError, match="Currency must be a 3-letter uppercase code"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="usd", salary_period="year", created_at=now).validate()

    with pytest.raises(InvalidJobDataError, match="Currency must be a 3-letter uppercase code"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="USD\n", salary_period="year", created_at=now).validate()

    # 6. Invalid salary period
    with pytest.raises(InvalidJobDataError, match="salary_period must be one of: hour, month, year"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="USD", salary_period="weekly", created_at=now).validate()

    # 7. Invalid URL scheme or malformed URL
    with pytest.raises(InvalidJobDataError, match="source_url must be a valid http or https URL"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", source_url="ftp://example.com/job", created_at=now).validate()

    with pytest.raises(InvalidJobDataError, match="source_url must be a valid http or https URL"):
        Job(id=uuid4(), user_id=user_id, title="Dev", company="Acme", source_url="http://[bad", created_at=now).validate()


# --- Use Case & Unit Tests ---

@pytest.mark.asyncio
async def test_job_use_case_isolation():
    repo = InMemoryJobRepository()
    service = JobService(repo)

    user1_id = uuid4()
    user2_id = uuid4()

    # Create job for User 1
    create_cmd = CreateJobCommand(
        user_id=user1_id,
        title="Backend Engineer",
        company="TechCorp",
        description="Python & FastAPI",
    )
    job1 = await service.create_job(create_cmd)
    assert job1.user_id == user1_id
    assert job1.title == "Backend Engineer"

    # User 1 sees job 1
    user1_jobs = await service.list_jobs(ListJobsQuery(user_id=user1_id))
    assert user1_jobs.total == 1
    assert len(user1_jobs.items) == 1
    assert user1_jobs.items[0].id == job1.id

    user1_get = await service.get_job_by_id(GetJobByIdQuery(job_id=job1.id, user_id=user1_id))
    assert user1_get.id == job1.id

    # User 2 cannot see job 1 in list
    user2_jobs = await service.list_jobs(ListJobsQuery(user_id=user2_id))
    assert user2_jobs.total == 0
    assert len(user2_jobs.items) == 0

    # User 2 getting job 1 raises JobNotFoundError (404)
    with pytest.raises(JobNotFoundError):
        await service.get_job_by_id(GetJobByIdQuery(job_id=job1.id, user_id=user2_id))


# --- API Auth & Isolation Integration Tests ---

@pytest.fixture
def auth_setup():
    settings = AuthSettings(
        secret_key="test-secret-key-for-jwt-service",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    jwt_service = JwtTokenService(settings=settings)
    hasher = Argon2PasswordHasher()

    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        hashed_password=hasher.hash("password123"),
        first_name="User",
        last_name="One",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        hashed_password=hasher.hash("password123"),
        first_name="User",
        last_name="Two",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    inactive_user = User(
        id=uuid4(),
        email="inactive@example.com",
        hashed_password=hasher.hash("password123"),
        first_name="Inactive",
        last_name="User",
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )

    user_repo = MockUserRepository({
        "user1@example.com": user1,
        "user2@example.com": user2,
        "inactive@example.com": inactive_user,
    })

    job_repo = InMemoryJobRepository()

    container = Container()
    container.pool.override(MagicMock())
    container.auth_settings.override(settings)
    container.user_repository.override(user_repo)
    container.job_repository.override(job_repo)
    container.wire(modules=[
        "backend.api.endpoints.jobs.create_job",
        "backend.api.endpoints.jobs.get_job",
        "backend.api.endpoints.jobs.list_jobs",
        "backend.api.endpoints.jobs.update_job",
        "backend.api.endpoints.jobs.delete_job",
        "backend.api.dependencies",
    ])

    from backend.api.main import build_app
    app = build_app()
    app.state.container = container

    token_user1 = jwt_service.create_access_token("user1@example.com")
    token_user2 = jwt_service.create_access_token("user2@example.com")
    token_inactive = jwt_service.create_access_token("inactive@example.com")

    yield app, job_repo, token_user1, token_user2, token_inactive, user1, user2

    container.unwire()


def test_api_job_crud_and_contract(auth_setup):
    app, job_repo, token_user1, token_user2, token_inactive, user1, user2 = auth_setup
    client = TestClient(app)

    # Assert exact route registration for /jobs and no /api/v1 routes
    job_routes = [(r.path, tuple(r.methods)) for r in app.routes if hasattr(r, "methods")]
    assert (
        sum(1 for path, methods in job_routes if path == "/jobs" and "POST" in methods) == 1
    )
    assert (
        sum(1 for path, methods in job_routes if path == "/jobs" and "GET" in methods) == 1
    )
    assert (
        sum(1 for path, methods in job_routes if path == "/jobs/{job_id}" and "GET" in methods) == 1
    )
    assert (
        sum(1 for path, methods in job_routes if path == "/jobs/{job_id}" and "PATCH" in methods) == 1
    )
    assert (
        sum(1 for path, methods in job_routes if path == "/jobs/{job_id}" and "DELETE" in methods) == 1
    )
    assert not any("/api/v1" in p for p, _ in job_routes)

    # 1. No token -> 401
    res_no_token = client.get("/jobs")
    assert res_no_token.status_code == 401
    assert res_no_token.headers.get("WWW-Authenticate") == "Bearer"

    # 2. Inactive user -> 403
    res_inactive = client.get("/jobs", headers={"Authorization": f"Bearer {token_inactive}"})
    assert res_inactive.status_code == 403

    # 3. User 1 creates job
    create_payload = {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "salary_min": 100000,
        "salary_max": 150000,
        "currency": "USD",
        "salary_period": "year",
        "user_id": str(user2.id),  # Malicious spoof attempt
    }
    res_create = client.post(
        "/jobs",
        json=create_payload,
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_create.status_code == 201
    job_data = res_create.json()
    job_id = job_data["id"]
    assert job_data["title"] == "Software Engineer"
    assert job_data["currency"] == "USD"
    assert job_data["application"] is None
    assert "user_id" not in job_data

    # Verify repository owner is user1
    stored_job = job_repo.jobs[0]
    assert stored_job.id == UUID(job_id)
    assert stored_job.user_id == user1.id

    # 4. User 1 gets job by ID -> 200
    res_get_u1 = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_u1.status_code == 200
    assert res_get_u1.json()["id"] == job_id

    # 5. User 2 gets User 1's job -> 404
    res_get_u2 = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_get_u2.status_code == 404
    assert res_get_u2.json()["detail"] == "Job not found"

    # 6. PATCH partial update (omitted vs null behavior)
    res_patch = client.patch(
        f"/jobs/{job_id}",
        json={"location": "Remote", "salary_min": 120000},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch.status_code == 200
    patch_data = res_patch.json()
    assert patch_data["location"] == "Remote"
    assert patch_data["salary_min"] == 120000
    assert patch_data["salary_max"] == 150000  # Omitted -> preserved

    res_patch_null = client.patch(
        f"/jobs/{job_id}",
        json={"location": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_null.status_code == 200
    assert res_patch_null.json()["location"] == "Remote"  # Explicit null for nullable field preserves prior value

    # 6b. PATCH foreign-owner -> 404
    res_patch_foreign = client.patch(
        f"/jobs/{job_id}",
        json={"location": "Elsewhere"},
        headers={"Authorization": f"Bearer {token_user2}"},
    )
    assert res_patch_foreign.status_code == 404
    assert res_patch_foreign.json()["detail"] == "Job not found"

    # 6c. PATCH title=null and company=null -> 422
    res_patch_bad_title = client.patch(
        f"/jobs/{job_id}",
        json={"title": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_bad_title.status_code == 422

    res_patch_bad_company = client.patch(
        f"/jobs/{job_id}",
        json={"company": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_bad_company.status_code == 422

    # 7. List jobs (paginated `{items, total, limit, offset}`)
    res_list_u1 = client.get("/jobs?q=Acme&limit=10&offset=0", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_list_u1.status_code == 200
    list_json = res_list_u1.json()
    assert list_json["total"] == 1
    assert len(list_json["items"]) == 1
    assert list_json["limit"] == 10
    assert list_json["offset"] == 0

    res_list_u2 = client.get("/jobs", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_list_u2.status_code == 200
    assert res_list_u2.json()["total"] == 0
    assert res_list_u2.json()["items"] == []

    # 8. Invalid domain payload -> 422
    res_bad_val = client.post(
        "/jobs",
        json={"title": "Dev", "company": "Acme", "source_url": "http://[bad"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_bad_val.status_code == 422
    assert "source_url must be a valid http or https URL" in str(res_bad_val.json())

    # 9. DELETE job (foreign -> 404, owner -> 204)
    res_del_foreign = client.delete(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_del_foreign.status_code == 404

    res_del_owner = client.delete(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_del_owner.status_code == 204

    res_get_del = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_del.status_code == 404


def test_cors_preflight(auth_setup):
    app, _, _, _, _, _, _ = auth_setup
    client = TestClient(app)

    res_cors = client.options(
        "/jobs/123",
        headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert res_cors.status_code == 200
    assert res_cors.headers.get("access-control-allow-origin") == "http://localhost"
    allowed_methods = res_cors.headers.get("access-control-allow-methods", "")
    assert "PATCH" in allowed_methods
    assert "DELETE" in allowed_methods


# --- Asyncpg Repository SQL Unit Tests ---

@pytest.mark.asyncio
async def test_asyncpg_job_repository_sql():
    mock_pool = MagicMock()
    mock_pool.execute = AsyncMock(return_value="UPDATE 1")
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.fetchval = AsyncMock(return_value=10)
    mock_pool.fetch = AsyncMock(return_value=[])

    repo = AsyncpgJobRepository(pool=mock_pool)

    job_id = uuid4()
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    job = Job(
        id=job_id,
        user_id=user_id,
        title="Senior Python Dev",
        company="StartupInc",
        created_at=now,
    )

    # Test create SQL
    await repo.create(job)
    mock_pool.execute.assert_called_once()
    create_args = mock_pool.execute.call_args[0]
    sql_create = create_args[0]
    assert "INSERT INTO jobs" in sql_create
    assert create_args[1] == job_id
    assert create_args[2] == user_id

    # Test update SQL & owner predicate
    mock_pool.execute.reset_mock()
    success = await repo.update(job)
    assert success is True
    update_args = mock_pool.execute.call_args[0]
    assert "UPDATE jobs" in update_args[0]
    assert "WHERE id = $1::UUID AND user_id = $2::UUID" in update_args[0]
    assert update_args[1] == job_id
    assert update_args[2] == user_id

    # Test delete SQL & owner predicate
    mock_pool.execute.reset_mock()
    mock_pool.execute.return_value = "DELETE 1"
    del_success = await repo.delete(job_id=job_id, user_id=user_id)
    assert del_success is True
    del_args = mock_pool.execute.call_args[0]
    assert "DELETE FROM jobs" in del_args[0]
    assert "WHERE id = $1::UUID AND user_id = $2::UUID" in del_args[0]
    assert del_args[1] == job_id
    assert del_args[2] == user_id

    # Test list_and_count SQL, escaping, and pagination
    items, total = await repo.list_and_count(user_id=user_id, q="100%_test", limit=5, offset=20)
    assert items == []
    assert total == 10

    count_args = mock_pool.fetchval.call_args[0]
    assert "SELECT COUNT(*)" in count_args[0]
    assert "ESCAPE '\\'" in count_args[0]
    assert count_args[2] == "%100\\%\\_test%"

    fetch_args = mock_pool.fetch.call_args[0]
    assert "ORDER BY j.created_at DESC, j.id DESC" in fetch_args[0]
    assert "LIMIT $3 OFFSET $4" in fetch_args[0]
    assert fetch_args[3] == 5
    assert fetch_args[4] == 20
