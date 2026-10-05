from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ImportStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


@dataclass(kw_only=True)
class JobImportFields:
    title: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    salary_period: Literal["hour", "month", "year"] | str | None = None
    technologies: list[str] | None = None
    source: str | None = None


@dataclass(kw_only=True)
class JobImportResult:
    status: ImportStatus
    source_url: str
    fields: JobImportFields
    reason_code: str | None = None
    message: str | None = None
