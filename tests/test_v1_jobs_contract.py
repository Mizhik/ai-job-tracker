from datetime import datetime, timezone
from uuid import uuid4, UUID
import pytest

from tests.test_job_isolation import auth_setup, InMemoryJobRepository
from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.commands.update_job import UpdateJobCommand
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.service import JobService
from backend.core.errors import InvalidJobDataError, JobNotFoundError
from backend.core.job import Job


@pytest.mark.asyncio
async def test_job_validation_rules():
    user_id = uuid4()

    # 1. Blank title or company
    job_blank_title = Job(
        id=uuid4(), user_id=user_id, title="   ", company="Acme", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="Title cannot be blank"):
        job_blank_title.validate()

    job_blank_company = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="Company cannot be blank"):
        job_blank_company.validate()

    # 2. Negative salary
    job_neg_salary = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=-10, currency="USD", salary_period="year", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="salary_min cannot be negative"):
        job_neg_salary.validate()

    # 3. Min > Max salary
    job_min_gt_max = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=100, salary_max=50, currency="USD", salary_period="year", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="salary_min cannot be greater than salary_max"):
        job_min_gt_max.validate()

    # 4. Numeric salary missing currency/period
    job_no_curr = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="Numeric salary requires both currency and salary_period"):
        job_no_curr.validate()

    # 5. Invalid currency code
    job_bad_curr = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="usd", salary_period="year", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="Currency must be a 3-letter uppercase code"):
        job_bad_curr.validate()

    # 6. Invalid salary period
    job_bad_period = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="USD", salary_period="weekly", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="salary_period must be one of: hour, month, year"):
        job_bad_period.validate()

    # 7. Invalid URL scheme or malformed URL
    job_bad_url = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", source_url="ftp://example.com/job", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="source_url must be a valid http or https URL"):
        job_bad_url.validate()

    job_malformed_url = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", source_url="http://[bad", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="source_url must be a valid http or https URL"):
        job_malformed_url.validate()

    # 8. Currency with trailing newline (re.fullmatch check)
    job_newline_curr = Job(
        id=uuid4(), user_id=user_id, title="Dev", company="Acme", salary_min=50000, currency="USD\n", salary_period="year", created_at=datetime.now(timezone.utc)
    )
    with pytest.raises(InvalidJobDataError, match="Currency must be a 3-letter uppercase code"):
        job_newline_curr.validate()


def test_v1_jobs_api_crud_and_contract(auth_setup):
    app, job_repo, token_u1, token_u2, _, u1, u2 = auth_setup
    from fastapi.testclient import TestClient
    client = TestClient(app)

    # 1. Unauthenticated -> 401 with {code, message, details} and WWW-Authenticate header
    res = client.get("/api/v1/jobs")
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"
    unauth_json = res.json()
    assert unauth_json["code"] == "unauthorized"
    assert "message" in unauth_json
    assert unauth_json["details"] == []

    # 1b. Inactive user -> 403 with {code, message, details}
    token_inactive = auth_setup[4]
    res_inactive = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token_inactive}"})
    assert res_inactive.status_code == 403
    inactive_json = res_inactive.json()
    assert inactive_json["code"] == "forbidden"
    assert inactive_json["details"] == []

    # 2. POST create valid job
    create_payload = {
        "title": "Senior Engineer",
        "company": "Tech Corp",
        "salary_min": 100000,
        "salary_max": 150000,
        "currency": "USD",
        "salary_period": "year",
        "source_url": "https://example.com/jobs/1",
    }
    res_create = client.post(
        "/api/v1/jobs",
        json=create_payload,
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_create.status_code == 201
    data = res_create.json()
    job_id = data["id"]
    assert data["title"] == "Senior Engineer"
    assert data["company"] == "Tech Corp"
    assert data["currency"] == "USD"
    assert data["application"] is None
    assert "user_id" not in data

    # 3. GET job v1 by ID (owner)
    res_get = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["id"] == job_id

    # 4. GET job v1 by ID (foreign user -> 404 with {code, message, details})
    res_foreign_get = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_u2}"},
    )
    assert res_foreign_get.status_code == 404
    err_body = res_foreign_get.json()
    assert err_body["code"] == "not_found"
    assert err_body["message"] == "Job not found"

    # 5. PATCH job v1 partial update
    patch_payload = {
        "location": "Remote",
        "salary_min": 120000,
    }
    res_patch = client.patch(
        f"/api/v1/jobs/{job_id}",
        json=patch_payload,
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_patch.status_code == 200
    patched_data = res_patch.json()
    assert patched_data["location"] == "Remote"
    assert patched_data["salary_min"] == 120000
    assert patched_data["salary_max"] == 150000
    assert patched_data["updated_at"] is not None

    # 6. PATCH job v1 explicit null clear field
    res_clear = client.patch(
        f"/api/v1/jobs/{job_id}",
        json={"location": None},
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_clear.status_code == 200
    assert res_clear.json()["location"] is None

    # 7. PATCH job v1 invalid title -> 422
    res_bad_title = client.patch(
        f"/api/v1/jobs/{job_id}",
        json={"title": "  "},
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_bad_title.status_code == 422
    assert res_bad_title.json()["code"] == "validation_error"

    # 8. GET list v1 with pagination & search
    client.post(
        "/api/v1/jobs",
        json={"title": "Data Scientist", "company": "AI Tech"},
        headers={"Authorization": f"Bearer {token_u1}"},
    )

    res_list = client.get(
        "/api/v1/jobs?q=Tech&limit=1&offset=0",
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_list.status_code == 200
    list_body = res_list.json()
    assert list_body["total"] == 2
    assert len(list_body["items"]) == 1
    assert list_body["limit"] == 1
    assert list_body["offset"] == 0

    # Test literal search escaping %
    res_search_percent = client.get(
        "/api/v1/jobs?q=%",
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_search_percent.status_code == 200
    assert res_search_percent.json()["total"] == 0

    # 9. DELETE job v1 (foreign -> 404)
    res_del_foreign = client.delete(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_u2}"},
    )
    assert res_del_foreign.status_code == 404

    # 10. DELETE job v1 (owner -> 204)
    res_del = client.delete(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_del.status_code == 204

    # Verify deleted
    res_get_del = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_get_del.status_code == 404


def test_cors_preflight_and_legacy_validation_handling(auth_setup):
    app, job_repo, token_u1, _, _, _, _ = auth_setup
    from fastapi.testclient import TestClient
    client = TestClient(app)

    # 1. Test CORS OPTIONS preflight request for PATCH and DELETE on v1
    res_cors = client.options(
        "/api/v1/jobs/123",
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

    # 2. Test legacy route validation error (returns standard FastAPI {"detail": [...]})
    res_legacy_val = client.post(
        "/jobs",
        json={"salary_min": "invalid_number"},
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_legacy_val.status_code == 422
    assert "detail" in res_legacy_val.json()

    # 3. Test legacy POST /jobs accepts currency & salary_period
    res_legacy_post = client.post(
        "/jobs",
        json={
            "title": "Legacy Dev",
            "company": "Legacy Corp",
            "salary_min": 80000,
            "currency": "USD",
            "salary_period": "year",
        },
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_legacy_post.status_code == 201
    assert res_legacy_post.json()["title"] == "Legacy Dev"

    # 4. Test legacy POST /jobs returns 422 for domain invariant violation (e.g. invalid title or salary without currency)
    res_legacy_domain_err = client.post(
        "/jobs",
        json={
            "title": "Legacy Dev 2",
            "company": "Legacy Corp",
            "salary_min": 80000,  # missing currency/period -> 422
        },
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_legacy_domain_err.status_code == 422
    assert "Numeric salary requires both currency and salary_period" in str(res_legacy_domain_err.json())

    # 5. Test malformed URL in v1 and legacy returns 422
    res_v1_malformed_url = client.post(
        "/api/v1/jobs",
        json={
            "title": "Malformed URL Job",
            "company": "Corp",
            "source_url": "http://[bad",
        },
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_v1_malformed_url.status_code == 422
    assert res_v1_malformed_url.json()["message"] == "source_url must be a valid http or https URL"

    res_legacy_malformed_url = client.post(
        "/jobs",
        json={
            "title": "Malformed URL Job Legacy",
            "company": "Corp",
            "source_url": "http://[bad",
        },
        headers={"Authorization": f"Bearer {token_u1}"},
    )
    assert res_legacy_malformed_url.status_code == 422
    assert "source_url must be a valid http or https URL" in str(res_legacy_malformed_url.json())
