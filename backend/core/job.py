from dataclasses import dataclass, field
import re
from urllib.parse import urlparse
from uuid import UUID

from .application import ApplicationSummary
from .base import Base
from .errors import InvalidJobDataError


@dataclass(kw_only=True)
class Job(Base):
    user_id: UUID
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
    application: ApplicationSummary | None = None

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidJobDataError("Title cannot be blank")
        if not self.company or not self.company.strip():
            raise InvalidJobDataError("Company cannot be blank")

        if self.salary_min is not None and self.salary_min < 0:
            raise InvalidJobDataError("salary_min cannot be negative")
        if self.salary_max is not None and self.salary_max < 0:
            raise InvalidJobDataError("salary_max cannot be negative")

        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise InvalidJobDataError("salary_min cannot be greater than salary_max")

        has_numeric_salary = self.salary_min is not None or self.salary_max is not None
        if has_numeric_salary:
            if not self.currency or not self.salary_period:
                raise InvalidJobDataError(
                    "Numeric salary requires both currency and salary_period"
                )

        if self.currency is not None:
            if not re.fullmatch(r"^[A-Z]{3}$", self.currency):
                raise InvalidJobDataError(
                    "Currency must be a 3-letter uppercase code"
                )

        if self.salary_period is not None:
            if self.salary_period not in ("hour", "month", "year"):
                raise InvalidJobDataError(
                    "salary_period must be one of: hour, month, year"
                )

        if self.source_url is not None:
            try:
                parsed = urlparse(self.source_url)
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    raise InvalidJobDataError(
                        "source_url must be a valid http or https URL"
                    )
            except ValueError:
                raise InvalidJobDataError(
                    "source_url must be a valid http or https URL"
                )


@dataclass(kw_only=True)
class JobMatch(Base):
    job_id: UUID
    user_id: UUID
    match_score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    resume_tips: list[str] = field(default_factory=list)
