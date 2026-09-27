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
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.service import JobService
from backend.core.errors import JobNotFoundError
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

    async def list(self, user_id: UUID) -> list[Job]:
        return [job for job in self.jobs if job.user_id == user_id]

    async def list_and_count(
        self,
        user_id: UUID,
        q: str | None = None,
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
    assert len(user1_jobs) == 1
    assert user1_jobs[0].id == job1.id

    user1_get = await service.get_job_by_id(GetJobByIdQuery(job_id=job1.id, user_id=user1_id))
    assert user1_get.id == job1.id

    # User 2 cannot see job 1 in list
    user2_jobs = await service.list_jobs(ListJobsQuery(user_id=user2_id))
    assert len(user2_jobs) == 0

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
    container.auth_settings.override(settings)
    container.user_repository.override(user_repo)
    container.job_repository.override(job_repo)
    container.wire(modules=[
        "backend.api.endpoints.jobs.create_job",
        "backend.api.endpoints.jobs.get_job",
        "backend.api.endpoints.jobs.list_jobs",
        "backend.api.endpoints.jobs.v1_jobs",
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


def test_api_job_isolation_and_auth(auth_setup):
    app, job_repo, token_user1, token_user2, token_inactive, user1, user2 = auth_setup
    client = TestClient(app)

    # 1. No token -> 401
    res_no_token = client.get("/jobs")
    assert res_no_token.status_code == 401
    assert res_no_token.headers.get("WWW-Authenticate") == "Bearer"

    # 2. Invalid token -> 401
    res_invalid_token = client.get("/jobs", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_invalid_token.status_code == 401
    assert res_invalid_token.headers.get("WWW-Authenticate") == "Bearer"

    # 3. Inactive user -> 403
    res_inactive = client.get("/jobs", headers={"Authorization": f"Bearer {token_inactive}"})
    assert res_inactive.status_code == 403

    # 4. User 1 creates job. Even if request body passes user_id, API ignores body owner and assigns user1
    create_payload = {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "user_id": str(user2.id),  # Malicious attempt to spoof owner
        "owner": str(user2.id),
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
    assert "user_id" not in job_data  # Response schema does not expose user_id

    # Verify in repository that job is owned by user1
    stored_job = job_repo.jobs[0]
    assert stored_job.id == UUID(job_id)
    assert stored_job.user_id == user1.id

    # 5. User 1 lists jobs -> gets 1 job
    res_list_u1 = client.get("/jobs", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_list_u1.status_code == 200
    u1_jobs = res_list_u1.json()
    assert len(u1_jobs) == 1
    assert u1_jobs[0]["id"] == job_id

    # 6. User 1 gets job by ID -> 200
    res_get_u1 = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_u1.status_code == 200
    assert res_get_u1.json()["id"] == job_id

    # 7. User 2 lists jobs -> empty list
    res_list_u2 = client.get("/jobs", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_list_u2.status_code == 200
    assert res_list_u2.json() == []

    # 8. User 2 gets User 1's job by ID -> 404 Not Found (same as missing ID)
    res_get_u2 = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_get_u2.status_code == 404
    assert res_get_u2.json()["detail"] == "Job not found"

    # 9. Querying non-existent UUID -> 404
    res_get_random = client.get(f"/jobs/{uuid4()}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_random.status_code == 404


# --- Asyncpg Repository SQL Unit Test ---

@pytest.mark.asyncio
async def test_asyncpg_job_repository_sql():
    mock_pool = MagicMock()
    mock_pool.execute = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)
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
    assert "user_id" in sql_create
    # Verify parameter bindings ($1..$13)
    assert create_args[1] == job_id
    assert create_args[2] == user_id
    assert create_args[3] == "Senior Python Dev"

    # Test get_by_id SQL
    await repo.get_by_id(job_id=job_id, user_id=user_id)
    mock_pool.fetchrow.assert_called_once()
    get_args = mock_pool.fetchrow.call_args[0]
    sql_get = get_args[0]
    assert "WHERE id = $1::UUID AND user_id = $2::UUID" in sql_get
    assert get_args[1] == job_id
    assert get_args[2] == user_id

    # Test list SQL
    await repo.list(user_id=user_id)
    mock_pool.fetch.assert_called_once()
    list_args = mock_pool.fetch.call_args[0]
    sql_list = list_args[0]
    assert "WHERE user_id = $1::UUID" in sql_list
    assert list_args[1] == user_id


@pytest.mark.asyncio
async def test_asyncpg_job_repository_v1_sql_operations():
    mock_pool = MagicMock()
    mock_pool.execute = AsyncMock(return_value="UPDATE 1")
    mock_pool.fetchval = AsyncMock(return_value=5)
    mock_pool.fetch = AsyncMock(return_value=[])

    repo = AsyncpgJobRepository(pool=mock_pool)

    job_id = uuid4()
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. Test update SQL and owner predicate
    job = Job(
        id=job_id,
        user_id=user_id,
        title="Lead Engineer",
        company="BigCorp",
        salary_min=100,
        salary_max=200,
        currency="USD",
        salary_period="year",
        created_at=now,
        updated_at=now,
    )
    success = await repo.update(job)
    assert success is True
    mock_pool.execute.assert_called_once()
    update_args = mock_pool.execute.call_args[0]
    sql_update = update_args[0]
    assert "UPDATE jobs" in sql_update
    assert "WHERE id = $1::UUID AND user_id = $2::UUID" in sql_update
    assert update_args[1] == job_id
    assert update_args[2] == user_id
    assert update_args[3] == "Lead Engineer"
    assert update_args[9] == "USD"
    assert update_args[10] == "year"

    # 2. Test delete SQL and owner predicate
    mock_pool.execute.reset_mock()
    mock_pool.execute.return_value = "DELETE 1"
    del_success = await repo.delete(job_id=job_id, user_id=user_id)
    assert del_success is True
    del_args = mock_pool.execute.call_args[0]
    sql_del = del_args[0]
    assert "DELETE FROM jobs" in sql_del
    assert "WHERE id = $1::UUID AND user_id = $2::UUID" in sql_del
    assert del_args[1] == job_id
    assert del_args[2] == user_id

    # 3. Test list_and_count with search, escaping %, _, and pagination offset
    items, total = await repo.list_and_count(
        user_id=user_id,
        q="100%_test",
        limit=10,
        offset=50,
    )
    assert items == []
    assert total == 5

    count_call_args = mock_pool.fetchval.call_args[0]
    assert "SELECT COUNT(*)" in count_call_args[0]
    assert "user_id = $1::UUID" in count_call_args[0]
    assert "ESCAPE '\\'" in count_call_args[0]
    assert count_call_args[1] == user_id
    assert count_call_args[2] == "%100\\%\\_test%"

    fetch_call_args = mock_pool.fetch.call_args[0]
    assert "ORDER BY created_at DESC, id DESC" in fetch_call_args[0]
    assert "LIMIT $3 OFFSET $4" in fetch_call_args[0]
    assert fetch_call_args[1] == user_id
    assert fetch_call_args[2] == "%100\\%\\_test%"
    assert fetch_call_args[3] == 10
    assert fetch_call_args[4] == 50
