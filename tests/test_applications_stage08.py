from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient

from backend.api.container import Container
from backend.app.applications import (
    ApplicationService,
    CreateApplicationCommand,
    DeleteApplicationCommand,
    GetApplicationByIdQuery,
    UpdateApplicationCommand,
)
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.service import JobService
from backend.core.application import Application, ApplicationStatus, ApplicationSummary
from backend.core.errors import (
    ApplicationAlreadyExistsError,
    ApplicationNotFoundError,
    JobNotFoundError,
)
from backend.core.job import Job
from backend.core.repository.application_repository import ApplicationRepository
from backend.core.repository.job_repository import JobRepository
from backend.core.user import User
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.postgres.application_repository import AsyncpgApplicationRepository
from backend.infrastructure.postgres.job_repository import AsyncpgJobRepository
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService


class InMemoryApplicationRepository(ApplicationRepository):
    def __init__(self):
        self.applications: list[Application] = []

    async def create(self, application: Application) -> None:
        for app in self.applications:
            if app.user_id == application.user_id and app.job_id == application.job_id:
                raise ApplicationAlreadyExistsError()
        self.applications.append(application)

    async def get_by_id(self, application_id: UUID, user_id: UUID) -> Application | None:
        for app in self.applications:
            if app.id == application_id and app.user_id == user_id:
                return app
        return None

    async def get_by_job_id(self, job_id: UUID, user_id: UUID) -> Application | None:
        for app in self.applications:
            if app.job_id == job_id and app.user_id == user_id:
                return app
        return None

    async def update(self, application: Application) -> bool:
        for idx, existing in enumerate(self.applications):
            if existing.id == application.id and existing.user_id == application.user_id:
                self.applications[idx] = application
                return True
        return False

    async def delete(self, application_id: UUID, user_id: UUID) -> bool:
        for idx, existing in enumerate(self.applications):
            if existing.id == application_id and existing.user_id == user_id:
                del self.applications[idx]
                return True
        return False


class InMemoryJobRepoWithApplications(JobRepository):
    def __init__(self, app_repo: InMemoryApplicationRepository):
        self.jobs: list[Job] = []
        self._app_repo = app_repo

    async def create(self, job: Job) -> None:
        self.jobs.append(job)

    async def get_by_id(self, job_id: UUID, user_id: UUID) -> Job | None:
        for job in self.jobs:
            if job.id == job_id and job.user_id == user_id:
                # Attach application summary if present
                app = next(
                    (a for a in self._app_repo.applications if a.job_id == job.id and a.user_id == user_id),
                    None,
                )
                if app:
                    job.application = ApplicationSummary(
                        id=app.id,
                        status=app.status,
                        applied_at=app.applied_at,
                    )
                else:
                    job.application = None
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

        # Attach application summaries
        for job in user_jobs:
            app = next(
                (a for a in self._app_repo.applications if a.job_id == job.id and a.user_id == user_id),
                None,
            )
            if app:
                job.application = ApplicationSummary(
                    id=app.id,
                    status=app.status,
                    applied_at=app.applied_at,
                )
            else:
                job.application = None

        if q and q.strip():
            term = q.strip().lower()
            user_jobs = [
                j for j in user_jobs
                if term in j.title.lower() or term in j.company.lower()
            ]

        if status and status.strip():
            st_term = status.strip().lower()
            if st_term == "saved":
                user_jobs = [j for j in user_jobs if j.application is None]
            else:
                user_jobs = [
                    j for j in user_jobs
                    if j.application is not None and j.application.status == st_term
                ]

        user_jobs.sort(key=lambda j: (j.created_at, j.id), reverse=True)
        total = len(user_jobs)
        paged = user_jobs[offset : offset + limit]
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
                # CASCADE delete application
                self._app_repo.applications = [
                    a for a in self._app_repo.applications
                    if not (a.job_id == job_id and a.user_id == user_id)
                ]
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


# --- 1. Domain & Enum Tests ---

def test_application_statuses():
    statuses = [s.value for s in ApplicationStatus]
    assert statuses == ["applied", "interview", "offer", "rejected", "withdrawn"]
    assert "new" not in statuses


# --- 2. Application Service Use Case Tests ---

@pytest.mark.asyncio
async def test_application_service_crud_and_invariants():
    app_repo = InMemoryApplicationRepository()
    job_repo = InMemoryJobRepoWithApplications(app_repo)
    service = ApplicationService(app_repo, job_repo)

    user_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. Job not found -> JobNotFoundError
    with pytest.raises(JobNotFoundError):
        await service.create_application(
            CreateApplicationCommand(user_id=user_id, job_id=uuid4())
        )

    # Create owned job
    job = Job(id=uuid4(), user_id=user_id, title="Backend Lead", company="Acme", created_at=now)
    await job_repo.create(job)

    # 2. Create application (default status=applied, applied_at=now)
    app1 = await service.create_application(
        CreateApplicationCommand(user_id=user_id, job_id=job.id)
    )
    assert app1.job_id == job.id
    assert app1.status == ApplicationStatus.APPLIED
    assert app1.notes is None
    assert app1.applied_at is not None

    # 3. Duplicate creation -> ApplicationAlreadyExistsError
    with pytest.raises(ApplicationAlreadyExistsError):
        await service.create_application(
            CreateApplicationCommand(user_id=user_id, job_id=job.id)
        )

    # 4. Get application by ID
    got_app = await service.get_application_by_id(
        GetApplicationByIdQuery(application_id=app1.id, user_id=user_id)
    )
    assert got_app.id == app1.id

    # 5. Get application for another user -> ApplicationNotFoundError
    with pytest.raises(ApplicationNotFoundError):
        await service.get_application_by_id(
            GetApplicationByIdQuery(application_id=app1.id, user_id=uuid4())
        )

    # 6. Update status (applied_at remains unchanged)
    original_applied_at = app1.applied_at
    updated_app = await service.update_application(
        UpdateApplicationCommand(
            application_id=app1.id,
            user_id=user_id,
            status=ApplicationStatus.INTERVIEW,
            notes="Scheduled phone screen",
            update_notes=True,
        )
    )
    assert updated_app.status == ApplicationStatus.INTERVIEW
    assert updated_app.applied_at == original_applied_at
    assert updated_app.notes == "Scheduled phone screen"

    # 7. Delete application
    await service.delete_application(
        DeleteApplicationCommand(application_id=app1.id, user_id=user_id)
    )

    # Getting deleted app -> ApplicationNotFoundError
    with pytest.raises(ApplicationNotFoundError):
        await service.get_application_by_id(
            GetApplicationByIdQuery(application_id=app1.id, user_id=user_id)
        )

    # 8. Re-creation after deletion succeeds
    app2 = await service.create_application(
        CreateApplicationCommand(user_id=user_id, job_id=job.id, status=ApplicationStatus.OFFER)
    )
    assert app2.status == ApplicationStatus.OFFER


# --- 3. API Integration Tests ---

@pytest.fixture
def api_setup():
    settings = AuthSettings(
        secret_key="test-secret-key-applications-stage08",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    jwt_service = JwtTokenService(settings=settings)
    hasher = Argon2PasswordHasher()

    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        hashed_password=hasher.hash("password123"),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        hashed_password=hasher.hash("password123"),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    user_repo = MockUserRepository({
        "user1@example.com": user1,
        "user2@example.com": user2,
    })

    app_repo = InMemoryApplicationRepository()
    job_repo = InMemoryJobRepoWithApplications(app_repo)

    container = Container()
    container.pool.override(MagicMock())
    container.auth_settings.override(settings)
    container.user_repository.override(user_repo)
    container.job_repository.override(job_repo)
    container.application_repository.override(app_repo)
    container.wire(modules=[
        "backend.api.endpoints.jobs.create_job",
        "backend.api.endpoints.jobs.get_job",
        "backend.api.endpoints.jobs.list_jobs",
        "backend.api.endpoints.jobs.update_job",
        "backend.api.endpoints.jobs.delete_job",
        "backend.api.endpoints.applications.create_application",
        "backend.api.endpoints.applications.get_application",
        "backend.api.endpoints.applications.update_application",
        "backend.api.endpoints.applications.delete_application",
        "backend.api.dependencies",
    ])

    from backend.api.main import build_app
    app = build_app()
    app.state.container = container

    token_user1 = jwt_service.create_access_token("user1@example.com")
    token_user2 = jwt_service.create_access_token("user2@example.com")

    yield app, job_repo, app_repo, token_user1, token_user2, user1, user2

    container.unwire()


def test_api_applications_full_contract(api_setup):
    app, job_repo, app_repo, token_user1, token_user2, user1, user2 = api_setup
    client = TestClient(app)

    # 1. Auth required -> 401
    res_no_auth = client.post(f"/jobs/{uuid4()}/application", json={})
    assert res_no_auth.status_code == 401

    # 2. Create job for User 1
    res_create_job = client.post(
        "/jobs",
        json={"title": "Frontend Eng", "company": "ViteCorp"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_create_job.status_code == 201
    job_data = res_create_job.json()
    job_id = job_data["id"]
    assert job_data["application"] is None

    # 3. User 2 tries creating application for User 1's job -> 404
    res_u2_app = client.post(
        f"/jobs/{job_id}/application",
        json={},
        headers={"Authorization": f"Bearer {token_user2}"},
    )
    assert res_u2_app.status_code == 404

    # 4. User 1 creates application with custom status, explicit applied_at and notes
    past_applied_at = "2026-09-01T10:00:00Z"
    res_u1_app = client.post(
        f"/jobs/{job_id}/application",
        json={
            "status": "interview",
            "notes": "First round completed",
            "applied_at": past_applied_at,
        },
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_u1_app.status_code == 201
    app_data = res_u1_app.json()
    app_id = app_data["id"]
    assert app_data["job_id"] == job_id
    assert app_data["status"] == "interview"
    assert app_data["notes"] == "First round completed"
    assert app_data["applied_at"] == past_applied_at
    assert app_data["created_at"].endswith("Z")
    assert "user_id" not in app_data

    # 5. Duplicate creation returns 409
    res_dup = client.post(
        f"/jobs/{job_id}/application",
        json={},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_dup.status_code == 409
    assert res_dup.json()["detail"] == "Application already exists for this job"

    # 6. GET /jobs/{job_id} returns application summary
    res_get_job = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_job.status_code == 200
    job_json = res_get_job.json()
    assert job_json["application"]["id"] == app_id
    assert job_json["application"]["status"] == "interview"
    assert job_json["application"]["applied_at"] == past_applied_at

    # 7. GET /applications/{application_id}
    res_get_app = client.get(f"/applications/{app_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_app.status_code == 200
    assert res_get_app.json()["id"] == app_id

    # User 2 getting User 1's application -> 404
    res_get_app_u2 = client.get(f"/applications/{app_id}", headers={"Authorization": f"Bearer {token_user2}"})
    assert res_get_app_u2.status_code == 404

    # 8. PATCH /applications/{application_id} validation and behavior
    # Empty PATCH body -> 422
    res_patch_empty = client.patch(
        f"/applications/{app_id}",
        json={},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_empty.status_code == 422

    # status: null -> 422
    res_patch_null_st = client.patch(
        f"/applications/{app_id}",
        json={"status": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_null_st.status_code == 422

    # applied_at: null -> 422
    res_patch_null_at = client.patch(
        f"/applications/{app_id}",
        json={"applied_at": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_null_at.status_code == 422

    # Naive applied_at -> 422
    res_patch_naive_at = client.patch(
        f"/applications/{app_id}",
        json={"applied_at": "2026-09-01T10:00:00"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_naive_at.status_code == 422

    # Valid status patch (withdrawn) -> 200, applied_at unchanged
    res_patch_st = client.patch(
        f"/applications/{app_id}",
        json={"status": "withdrawn"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_st.status_code == 200
    assert res_patch_st.json()["status"] == "withdrawn"
    assert res_patch_st.json()["applied_at"] == past_applied_at
    assert res_patch_st.json()["notes"] == "First round completed"  # Omitted -> preserved

    # notes: null -> clears notes
    res_patch_clear_notes = client.patch(
        f"/applications/{app_id}",
        json={"notes": None},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_clear_notes.status_code == 200
    assert res_patch_clear_notes.json()["notes"] is None

    # notes: "" -> sets empty string
    res_patch_empty_notes = client.patch(
        f"/applications/{app_id}",
        json={"notes": ""},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_empty_notes.status_code == 200
    assert res_patch_empty_notes.json()["notes"] == ""

    # 9. GET /jobs filtering by status (`saved`, application statuses)
    # Create a second job without application for User 1
    client.post(
        "/jobs",
        json={"title": "Backend Eng", "company": "PythonInc"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )

    # Filter status=saved -> returns Backend Eng only
    res_saved = client.get("/jobs?status=saved", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_saved.status_code == 200
    assert res_saved.json()["total"] == 1
    assert res_saved.json()["items"][0]["title"] == "Backend Eng"

    # Filter status=withdrawn -> returns Frontend Eng
    res_withdrawn = client.get("/jobs?status=withdrawn", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_withdrawn.status_code == 200
    assert res_withdrawn.json()["total"] == 1
    assert res_withdrawn.json()["items"][0]["title"] == "Frontend Eng"

    # Filter status=offer -> total=0
    res_offer = client.get("/jobs?status=offer", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_offer.status_code == 200
    assert res_offer.json()["total"] == 0

    # Invalid status filter -> 422
    res_bad_st = client.get("/jobs?status=new", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_bad_st.status_code == 422

    # 10. Deleting job cascades to application
    res_del_job = client.delete(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_del_job.status_code == 204

    # Getting deleted app -> 404
    res_get_del_app = client.get(f"/applications/{app_id}", headers={"Authorization": f"Bearer {token_user1}"})
    assert res_get_del_app.status_code == 404


def test_patch_extra_unknown_keys_rejected(api_setup):
    app, job_repo, app_repo, token_user1, token_user2, user1, user2 = api_setup
    client = TestClient(app)

    # Create job and application for user1
    res_job = client.post(
        "/jobs",
        json={"title": "Dev", "company": "Co"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    job_id = res_job.json()["id"]

    res_app = client.post(
        f"/jobs/{job_id}/application",
        json={},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    app_id = res_app.json()["id"]

    # 1. Unknown-only keys in PATCH body -> 422
    res_extra_only = client.patch(
        f"/applications/{app_id}",
        json={"foo": 1},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_extra_only.status_code == 422

    # 2. Unknown key alongside valid key in PATCH body -> 422
    res_extra_and_valid = client.patch(
        f"/applications/{app_id}",
        json={"foo": 1, "status": "interview"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_extra_and_valid.status_code == 422


def test_applied_at_numeric_and_non_string_types_rejected(api_setup):
    app, job_repo, app_repo, token_user1, token_user2, user1, user2 = api_setup
    client = TestClient(app)

    res_job = client.post(
        "/jobs",
        json={"title": "Dev", "company": "Co"},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    job_id = res_job.json()["id"]

    # 1. Numeric Unix timestamp on POST -> 422
    res_post_num = client.post(
        f"/jobs/{job_id}/application",
        json={"applied_at": 1234567890},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_post_num.status_code == 422

    # Create valid application
    res_app = client.post(
        f"/jobs/{job_id}/application",
        json={},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    app_id = res_app.json()["id"]

    # 2. Numeric Unix timestamp on PATCH -> 422
    res_patch_num = client.patch(
        f"/applications/{app_id}",
        json={"applied_at": 1234567890},
        headers={"Authorization": f"Bearer {token_user1}"},
    )
    assert res_patch_num.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_post_application_isolation():
    app_repo = InMemoryApplicationRepository()
    job_repo = InMemoryJobRepoWithApplications(app_repo)
    service = ApplicationService(app_repo, job_repo)

    user_id = uuid4()
    now = datetime.now(timezone.utc)
    job = Job(id=uuid4(), user_id=user_id, title="DevOps", company="CloudInc", created_at=now)
    await job_repo.create(job)

    # Simulate concurrent requests to create application for same job
    cmd1 = CreateApplicationCommand(user_id=user_id, job_id=job.id)
    cmd2 = CreateApplicationCommand(user_id=user_id, job_id=job.id)

    results = await asyncio.gather(
        service.create_application(cmd1),
        service.create_application(cmd2),
        return_exceptions=True,
    )

    successes = [r for r in results if isinstance(r, Application)]
    failures = [r for r in results if isinstance(r, ApplicationAlreadyExistsError)]

    assert len(successes) == 1
    assert len(failures) == 1


# --- 4. Asyncpg Repositories SQL & Exception Mapping Unit Tests ---

@pytest.mark.asyncio
async def test_asyncpg_application_repository_sql_and_exception_mapping():
    mock_pool = MagicMock()
    mock_pool.execute = AsyncMock()
    mock_pool.fetchrow = AsyncMock()

    app_repo = AsyncpgApplicationRepository(pool=mock_pool)

    app = Application(
        id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        status=ApplicationStatus.APPLIED,
        notes="Testing notes",
        applied_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Test create translates asyncpg UniqueViolationError to ApplicationAlreadyExistsError
    mock_pool.execute.side_effect = asyncpg.UniqueViolationError("duplicate key")
    with pytest.raises(ApplicationAlreadyExistsError):
        await app_repo.create(app)

    # Test create success
    mock_pool.execute.side_effect = None
    await app_repo.create(app)
    mock_pool.execute.assert_called()


# --- 5. Migration Fixture Preflight & Safety Tests ---

def test_migration_preflight_checks_sql_contents():
    # Verify migration file contains all required preflight checks and NOT NULL enforcement
    with open("migrations/005_applications_stage08.sql", "r") as f:
        sql = f.read()

    assert "NULL user_id, job_id, or applied_at" in sql
    assert "UPPER(status::text) = 'NEW'" in sql
    assert "unmappable status value" in sql
    assert "application user_id does not match job user_id owner" in sql
    assert "duplicate applications found" in sql
    assert "notes array contains embedded NULL elements" in sql
    assert "ALTER TABLE applications ALTER COLUMN user_id SET NOT NULL;" in sql
    assert "ALTER TABLE applications ALTER COLUMN job_id SET NOT NULL;" in sql
    assert "jobs_id_user_id_key" in sql
    assert "fk_applications_job_user" in sql
    assert "idx_applications_user_status" in sql


def test_migration_rollback_safety_checks_sql_contents():
    # Verify rollback file contains data-safety guards and schema restoration
    with open("migrations/005_applications_stage08.rollback.sql", "r") as f:
        rollback_sql = f.read()

    assert "applications contains withdrawn status which cannot be converted to legacy ApplicationStatus enum" in rollback_sql
    assert "applications contains multiline or empty-string notes which cannot be converted back to VARCHAR[] losslessly" in rollback_sql
    assert "ALTER TABLE applications ALTER COLUMN user_id DROP NOT NULL;" in rollback_sql
    assert "ALTER TABLE applications ALTER COLUMN job_id DROP NOT NULL;" in rollback_sql
    assert "DROP COLUMN IF EXISTS created_at" in rollback_sql
    assert "applied_at DROP NOT NULL" in rollback_sql
    assert "updated_at DROP NOT NULL" in rollback_sql
