from dataclasses import dataclass, field
from uuid import UUID

from .base import Base


@dataclass(kw_only=True)
class Job(Base):
    user_id: UUID
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None


@dataclass(kw_only=True)
class JobMatch(Base):
    job_id: UUID
    user_id: UUID
    match_score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    resume_tips: list[str] = field(default_factory=list)
