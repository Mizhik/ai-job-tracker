from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.commands.update_job import UNSET, UpdateJobCommand


class ErrorDetail(BaseModel):
    loc: list[str | int] | None = None
    msg: str
    type: str | None = None


class V1ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | list[dict[str, Any]] | None = None


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


class JobV1CreateInput(BaseModel):
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


class JobV1UpdateInput(BaseModel):
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

    def to_command(self, job_id: UUID, user_id: UUID) -> UpdateJobCommand:
        fields_set = self.model_fields_set
        return UpdateJobCommand(
            job_id=job_id,
            user_id=user_id,
            title=self.title if "title" in fields_set else UNSET,
            company=self.company if "company" in fields_set else UNSET,
            description=self.description if "description" in fields_set else UNSET,
            location=self.location if "location" in fields_set else UNSET,
            salary_min=self.salary_min if "salary_min" in fields_set else UNSET,
            salary_max=self.salary_max if "salary_max" in fields_set else UNSET,
            currency=self.currency if "currency" in fields_set else UNSET,
            salary_period=self.salary_period if "salary_period" in fields_set else UNSET,
            technologies=self.technologies if "technologies" in fields_set else UNSET,
            source_url=self.source_url if "source_url" in fields_set else UNSET,
            source=self.source if "source" in fields_set else UNSET,
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
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class JobV1Response(BaseModel):
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
    application: None = None
    created_at: datetime
    updated_at: datetime | None = None


class JobV1ListResponse(BaseModel):
    items: list[JobV1Response]
    total: int
    limit: int
    offset: int
