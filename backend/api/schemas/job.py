from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from backend.api.schemas.application import ApplicationSummaryResponse
from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.commands.update_job import UpdateJobCommand


class JobCreateInput(BaseModel):
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: str | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None

    def to_command(self, user_id: UUID) -> CreateJobCommand:
        return CreateJobCommand(
            user_id=user_id,
            title=self.title,
            company=self.company,
            description=self.description,
            location=self.location,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            currency=self.currency,
            salary_period=self.salary_period,
            technologies=self.technologies,
            source_url=self.source_url,
            source=self.source,
        )


class JobUpdateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: str | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None

    @field_validator("title", "company", mode="before")
    @classmethod
    def check_not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Field cannot be null")
        return value

    def to_command(self, job_id: UUID, user_id: UUID) -> UpdateJobCommand:
        return UpdateJobCommand(
            job_id=job_id,
            user_id=user_id,
            title=self.title,
            company=self.company,
            description=self.description,
            location=self.location,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            currency=self.currency,
            salary_period=self.salary_period,
            technologies=self.technologies,
            source_url=self.source_url,
            source=self.source,
        )


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: str | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None
    application: ApplicationSummaryResponse | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    limit: int
    offset: int
