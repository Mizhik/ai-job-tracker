from uuid import UUID

from pydantic import Field

from .base import Base


class Job(Base):
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


class JobMatch(Base):
    job_id: UUID
    user_id: UUID
    match_score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    resume_tips: list[str] = Field(default_factory=list)
