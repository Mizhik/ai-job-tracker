from typing import Literal
from pydantic import BaseModel, HttpUrl, Field


class ImportPreviewRequest(BaseModel):
    url: HttpUrl = Field(..., description="The job posting URL to import preview from")


class JobImportFieldsSchema(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: Literal["hour", "month", "year"] | None = None
    technologies: list[str] | None = None
    source: str | None = None


class ImportPreviewResponse(BaseModel):
    status: Literal["complete", "partial", "unavailable"]
    source_url: str
    fields: JobImportFieldsSchema
    reason_code: str | None = None
    message: str | None = None
