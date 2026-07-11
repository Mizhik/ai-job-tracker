from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


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
