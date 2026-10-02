import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.api.container import Container
from backend.app.jobs.commands.import_job_preview import ImportJobPreviewUseCase, _to_clean_int
from backend.core.abc.job_import import JobUrlExtractorPort
from backend.core.job_import import ImportStatus, JobImportFields
from backend.core.user import User
from backend.infrastructure.gemini_client import GeminiClient
from backend.infrastructure.postgres.pool.settings import DBSettings
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.settings.gemini import GeminiSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService


# --- Fake Extractor Port for Controlled Testing ---

class FakeJobUrlExtractor(JobUrlExtractorPort):
    def __init__(
        self,
        fields: JobImportFields | None = None,
        reason_code: str | None = None,
        message: str | None = None,
    ):
        self.fields = fields
        self.reason_code = reason_code
        self.message = message
        self.call_count = 0

    async def extract_job_fields_from_url(
        self, source_url: str
    ) -> tuple[JobImportFields | None, str | None, str | None]:
        self.call_count += 1
        return self.fields, self.reason_code, self.message


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


# --- Use Case & Field Normalization Tests ---

def test_to_clean_int_precision_and_robustness():
    assert _to_clean_int(123) == 123
    assert _to_clean_int("123") == 123
    assert _to_clean_int(123.0) == 123
    assert _to_clean_int(123.5) is None  # fractional float discarded
    assert _to_clean_int("123.5") is None  # fractional string discarded
    assert _to_clean_int(float("nan")) is None
    assert _to_clean_int(float("inf")) is None
    assert _to_clean_int(-500) is None
    assert _to_clean_int(True) is None
    assert _to_clean_int("nan") is None


@pytest.mark.asyncio
async def test_use_case_complete_normalization():
    raw_fields = JobImportFields(
        title="  Senior Backend Dev  ",
        company="  Global Tech  ",
        description="  Build Python services  ",
        location=" Remote ",
        salary_min=3000,
        salary_max=5000,
        currency="usd",
        salary_period="MONTH",
        technologies=[" Python ", "FastAPI", "Python", ""],
        source=" Djinni ",
    )
    extractor = FakeJobUrlExtractor(fields=raw_fields)

    use_case = ImportJobPreviewUseCase(extractor=extractor)
    result = await use_case.execute("https://example.com/jobs/42")

    assert result.status == ImportStatus.COMPLETE
    assert result.source_url == "https://example.com/jobs/42"
    assert result.fields.title == "Senior Backend Dev"
    assert result.fields.company == "Global Tech"
    assert result.fields.description == "Build Python services"
    assert result.fields.location == "Remote"
    assert result.fields.salary_min == 3000
    assert result.fields.salary_max == 5000
    assert result.fields.currency == "USD"
    assert result.fields.salary_period == "month"
    assert result.fields.technologies == ["Python", "FastAPI"]
    assert result.fields.source == "Djinni"


@pytest.mark.asyncio
async def test_import_source_url_is_not_duplicated_in_source_field():
    use_case = ImportJobPreviewUseCase(
        FakeJobUrlExtractor(JobImportFields(title="Engineer", company="Acme", source="https://djinni.co/jobs/123")),
    )

    result = await use_case.execute("https://djinni.co/jobs/123")

    assert result.source_url == "https://djinni.co/jobs/123"
    assert result.fields.source == "djinni.co"


@pytest.mark.asyncio
async def test_use_case_partial_when_title_missing():
    raw_fields = JobImportFields(
        title=None,
        company="Acme Corp",
        salary_min=2000,
        currency="EUR",
        salary_period="month",
    )
    extractor = FakeJobUrlExtractor(fields=raw_fields)

    use_case = ImportJobPreviewUseCase(extractor=extractor)
    result = await use_case.execute("https://example.com/jobs/1")

    assert result.status == ImportStatus.PARTIAL
    assert result.fields.title is None
    assert result.fields.company == "Acme Corp"


@pytest.mark.asyncio
async def test_use_case_discard_invalid_salary_and_currency():
    raw_fields = JobImportFields(
        title="Dev",
        company="Acme",
        salary_min=5000,
        salary_max=3000,  # min > max -> invalid!
        currency="INVALID_CODE",
        salary_period="weekly",
    )
    extractor = FakeJobUrlExtractor(fields=raw_fields)

    use_case = ImportJobPreviewUseCase(extractor=extractor)
    result = await use_case.execute("https://example.com/jobs/1")

    assert result.status == ImportStatus.COMPLETE
    assert result.fields.salary_min is None
    assert result.fields.salary_max is None
    assert result.fields.currency is None
    assert result.fields.salary_period is None


@pytest.mark.asyncio
async def test_use_case_unavailable_when_extractor_fails():
    extractor = FakeJobUrlExtractor(
        fields=None,
        reason_code="access_denied",
        message="Access denied by target website",
    )

    use_case = ImportJobPreviewUseCase(extractor=extractor)
    result = await use_case.execute("https://example.com/jobs/blocked")

    assert result.status == ImportStatus.UNAVAILABLE
    assert result.reason_code == "access_denied"
    assert "Access denied" in result.message


@pytest.mark.asyncio
async def test_salary_discarded_when_missing_currency_or_period():
    # Salary given but currency missing -> numeric salary must be discarded
    raw_fields1 = JobImportFields(
        title="Dev",
        company="Acme",
        salary_min=3000,
        salary_max=5000,
        currency=None,
        salary_period="month",
    )
    uc1 = ImportJobPreviewUseCase(FakeJobUrlExtractor(raw_fields1))
    res1 = await uc1.execute("https://example.com/job")
    assert res1.fields.salary_min is None
    assert res1.fields.salary_max is None
    assert res1.fields.currency is None

    # Salary given but salary_period missing -> numeric salary must be discarded
    raw_fields2 = JobImportFields(
        title="Dev",
        company="Acme",
        salary_min=3000,
        currency="USD",
        salary_period=None,
    )
    uc2 = ImportJobPreviewUseCase(FakeJobUrlExtractor(raw_fields2))
    res2 = await uc2.execute("https://example.com/job")
    assert res2.fields.salary_min is None
    assert res2.fields.currency is None
    assert res2.fields.salary_period is None


# --- Gemini Adapter Integration Tests ---

@pytest.mark.asyncio
async def test_gemini_client_missing_api_key():
    settings = GeminiSettings(gemini_api_key="")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url("https://example.com/job")
    assert fields is None
    assert reason == "provider_unavailable"
    assert "unavailable" in msg.lower()


@pytest.mark.asyncio
async def test_gemini_client_success_grounded(monkeypatch):
    target_url = "https://jobs.dou.ua/companies/epam-systems/vacancies/375181/"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [
                    {
                        "url": target_url,
                        "status": "success",
                    }
                ],
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": True,
                            "title": "Python / Embedded Engineer",
                            "company": "EPAM",
                            "description": "Embedded Python development role",
                            "location": "Remote",
                            "salary_min": 4000,
                            "salary_max": 6000,
                            "currency": "USD",
                            "salary_period": "month",
                            "technologies": ["Python", "C++", "Linux"],
                            "source": "DOU",
                        }),
                    }
                ],
            },
        ]
    }

    requests_recorded = []

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        class FakeRequest:
            pass
        req = FakeRequest()
        req.url = url
        req.headers = headers
        req.json_body = json
        requests_recorded.append(req)
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings = GeminiSettings(gemini_api_key="fake-gemini-key")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert len(requests_recorded) == 1
    req = requests_recorded[0]
    assert req.url == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert req.headers.get("x-goog-api-key") == "fake-gemini-key"
    assert req.json_body["model"] == "gemini-3.5-flash"
    assert req.json_body["store"] is False
    assert req.json_body["tools"] == [{"type": "url_context"}]
    assert isinstance(req.json_body["system_instruction"], str)
    assert req.json_body["input"] == f"Please read the job posting at this URL and extract facts: {target_url}"

    assert fields is not None
    assert reason is None
    assert fields.title == "Python / Embedded Engineer"
    assert fields.company == "EPAM"
    assert fields.source == "DOU"


@pytest.mark.asyncio
async def test_gemini_client_grounded_partial(monkeypatch):
    target_url = "https://djinni.co/jobs/847387-ai-ops-specialist/"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [{"url": target_url, "status": "success"}],
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": True,
                            "title": "AI Ops Specialist",
                            "company": None,
                            "description": "Looking for AI Ops",
                            "location": "Kyiv",
                            "salary_min": None,
                            "salary_max": None,
                            "currency": None,
                            "salary_period": None,
                            "technologies": ["AI", "Python"],
                            "source": "Djinni",
                        }),
                    }
                ],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is not None
    assert reason is None
    assert fields.title == "AI Ops Specialist"
    assert fields.company is None


@pytest.mark.asyncio
async def test_gemini_client_incomplete_interaction_status(monkeypatch):
    target_url = "https://example.com/job"
    mock_payload = {
        "status": "in_progress",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [{"url": target_url, "status": "success"}],
            },
            {
                "type": "model_output",
                "content": [{"type": "text", "text": json.dumps({"is_job_posting": True, "title": "Dev", "company": "Acme"})}],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "provider_unavailable"


@pytest.mark.asyncio
async def test_gemini_client_missing_retrieval_evidence(monkeypatch):
    target_url = "https://example.com/job"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": True,
                            "title": "Unverified Job",
                            "company": "Fake Corp",
                        }),
                    }
                ],
            }
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings = GeminiSettings(gemini_api_key="fake-key")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "unreadable"


@pytest.mark.asyncio
async def test_gemini_client_unrelated_url_evidence(monkeypatch):
    target_url = "https://example.com/job"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [
                    {
                        "url": "https://other-site.com/unrelated",
                        "status": "success",
                    }
                ],
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": True,
                            "title": "Other Job",
                            "company": "Other Corp",
                        }),
                    }
                ],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings = GeminiSettings(gemini_api_key="fake-key")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "unreadable"


@pytest.mark.asyncio
async def test_gemini_client_failed_retrieval_status(monkeypatch):
    target_url = "https://example.com/forbidden"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [
                    {
                        "url": target_url,
                        "status": "access_denied",
                    }
                ],
            }
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings = GeminiSettings(gemini_api_key="fake-key")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "access_denied"


@pytest.mark.asyncio
async def test_gemini_client_non_boolean_is_error(monkeypatch):
    target_url = "https://example.com/job"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": "false",
                "result": [{"url": target_url, "status": "success"}],
            },
            {
                "type": "model_output",
                "content": [{"type": "text", "text": json.dumps({"is_job_posting": True, "title": "Dev", "company": "Acme"})}],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "unreadable"


@pytest.mark.asyncio
async def test_gemini_client_non_boolean_is_job_posting(monkeypatch):
    target_url = "https://example.com/job"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [{"url": target_url, "status": "success"}],
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": "true",
                            "title": "Dev",
                            "company": "Acme",
                        }),
                    }
                ],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "unreadable"


@pytest.mark.asyncio
async def test_gemini_client_non_job_posting(monkeypatch):
    target_url = "https://example.com/about-us"
    mock_payload = {
        "status": "completed",
        "steps": [
            {
                "type": "url_context_result",
                "is_error": False,
                "result": [{"url": target_url, "status": "success"}],
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_job_posting": False,
                            "title": None,
                            "company": "Company Info Page",
                        }),
                    }
                ],
            },
        ],
    }

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings = GeminiSettings(gemini_api_key="fake-key")
    client = GeminiClient(settings)

    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "unreadable"
    assert "not contain a job posting" in msg


@pytest.mark.asyncio
async def test_gemini_client_malformed_outer_json_bytes(monkeypatch):
    target_url = "https://example.com/job"

    async def mock_post_malformed(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, content=b"invalid raw json bytes {{{")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_malformed)

    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "provider_unavailable"


@pytest.mark.asyncio
async def test_gemini_client_malformed_json_text_and_no_text_output(monkeypatch):
    target_url = "https://example.com/job"

    # 1. No text output in model_output step
    mock_payload1 = {
        "status": "completed",
        "steps": [
            {"type": "url_context_result", "is_error": False, "result": [{"url": target_url, "status": "success"}]},
            {"type": "model_output", "content": []},
        ],
    }

    async def mock_post1(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload1)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post1)
    client = GeminiClient(GeminiSettings(gemini_api_key="fake-key"))
    fields1, reason1, _ = await client.extract_job_fields_from_url(target_url)
    assert fields1 is None
    assert reason1 == "provider_unavailable"

    # 2. Malformed JSON inside text block
    mock_payload2 = {
        "status": "completed",
        "steps": [
            {"type": "url_context_result", "is_error": False, "result": [{"url": target_url, "status": "success"}]},
            {"type": "model_output", "content": [{"type": "text", "text": "{bad_json: missing_quotes}"}]},
        ],
    }

    async def mock_post2(self, url, headers=None, json=None, **kwargs):
        return httpx.Response(200, json=mock_payload2)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post2)
    fields2, reason2, _ = await client.extract_job_fields_from_url(target_url)
    assert fields2 is None
    assert reason2 == "provider_unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code,expected_msg_fragment",
    [
        (401, "credentials invalid or access denied"),
        (403, "credentials invalid or access denied"),
        (429, "rate limit exceeded"),
        (503, "returned an error"),
    ],
)
async def test_gemini_client_http_status_errors(monkeypatch, status_code, expected_msg_fragment):
    target_url = "https://example.com/job"
    recorded_requests = []

    async def mock_post_status(self, url, headers=None, json=None, **kwargs):
        recorded_requests.append((url, headers))
        return httpx.Response(status_code, json={"error": f"HTTP {status_code}"})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_status)

    client = GeminiClient(GeminiSettings(gemini_api_key="test-api-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert len(recorded_requests) == 1
    assert fields is None
    assert reason == "provider_unavailable"
    assert expected_msg_fragment in msg.lower()


@pytest.mark.asyncio
async def test_gemini_client_timeout_error(monkeypatch):
    target_url = "https://example.com/job"

    async def mock_post_timeout(*a, **k):
        raise httpx.TimeoutException("Connection timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_timeout)

    client = GeminiClient(GeminiSettings(gemini_api_key="test-api-key"))
    fields, reason, msg = await client.extract_job_fields_from_url(target_url)

    assert fields is None
    assert reason == "provider_unavailable"
    assert "timed out" in msg.lower()


# --- API Endpoint Contract & Rate Limit Tests ---

@pytest.fixture
def api_setup():
    auth_settings = AuthSettings(
        secret_key="test-secret-key-for-jwt-service",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    db_settings = DBSettings(
        dbname="test_db",
        user="test_user",
        password="test_password",
        address="localhost:5432",
    )
    jwt_service = JwtTokenService(settings=auth_settings)

    active_user = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed_pass",
        first_name="Active",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    user_repo = MockUserRepository({"user@example.com": active_user})

    fake_extractor = FakeJobUrlExtractor(
        fields=JobImportFields(
            title="Senior Python Engineer",
            company="Awesome Startup",
            salary_min=4000,
            salary_max=6000,
            currency="USD",
            salary_period="month",
            technologies=["Python", "FastAPI", "PostgreSQL"],
        )
    )

    fake_use_case = ImportJobPreviewUseCase(extractor=fake_extractor)

    container = Container()
    container.pool.override(MagicMock())
    container.db_settings.override(db_settings)
    container.auth_settings.override(auth_settings)
    container.user_repository.override(user_repo)
    container.import_job_preview_use_case.override(fake_use_case)
    container.wire(modules=[
        "backend.api.endpoints.jobs.import_job_preview",
        "backend.api.dependencies",
    ])

    from backend.api.main import build_app
    app = build_app()
    app.state.container = container

    token = jwt_service.create_access_token("user@example.com")

    yield app, token, fake_extractor

    container.unwire()


def test_import_job_preview_api_flow(api_setup):
    app, token, fake_extractor = api_setup
    client = TestClient(app)

    # 1. Unauthenticated -> 401
    res_no_auth = client.post("/jobs/import-preview", json={"url": "https://example.com/job"})
    assert res_no_auth.status_code == 401

    # 2. Invalid URL -> 422
    res_invalid_url = client.post(
        "/jobs/import-preview",
        json={"url": "not-a-valid-url"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_invalid_url.status_code == 422

    # 3. Successful complete preview -> 200
    res_success = client.post(
        "/jobs/import-preview",
        json={"url": "https://example.com/jobs/123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_success.status_code == 200
    data = res_success.json()
    assert data["status"] == "complete"
    assert data["source_url"] == "https://example.com/jobs/123"
    assert data["fields"]["title"] == "Senior Python Engineer"
    assert data["fields"]["company"] == "Awesome Startup"
    assert data["fields"]["salary_min"] == 4000
    assert data["fields"]["salary_max"] == 6000
    assert data["fields"]["currency"] == "USD"
    assert data["fields"]["salary_period"] == "month"
    assert data["fields"]["technologies"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["reason_code"] is None

    # 4. Unavailable preview -> 200 with status "unavailable" (never 500)
    fake_extractor.fields = None
    fake_extractor.reason_code = "access_denied"
    fake_extractor.message = "Access denied by target website"

    res_denied = client.post(
        "/jobs/import-preview",
        json={"url": "https://example.com/jobs/forbidden"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_denied.status_code == 200
    denied_data = res_denied.json()
    assert denied_data["status"] == "unavailable"
    assert denied_data["reason_code"] == "access_denied"
    assert "Access denied" in denied_data["message"]


def test_import_job_preview_api_rate_limit(api_setup):
    app, token, fake_extractor = api_setup
    client = TestClient(app)

    fake_extractor.fields = JobImportFields(title="Engineer", company="Company")
    fake_extractor.call_count = 0

    # Execute 5 allowed requests
    for i in range(5):
        res = client.post(
            "/jobs/import-preview",
            json={"url": f"https://example.com/jobs/{i+100}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "complete"

    initial_calls = fake_extractor.call_count
    assert initial_calls == 5

    # 6th request within window exceeds rate limit
    res_rate_limited = client.post(
        "/jobs/import-preview",
        json={"url": "https://example.com/jobs/999"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_rate_limited.status_code == 200
    limited_data = res_rate_limited.json()
    assert limited_data["status"] == "unavailable"
    assert limited_data["reason_code"] == "rate_limit_exceeded"
    assert "Rate limit exceeded" in limited_data["message"]

    # Extractor must NOT have been called for rejected request
    assert fake_extractor.call_count == initial_calls
