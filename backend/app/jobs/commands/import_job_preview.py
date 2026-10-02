import logging
import math
import re
from typing import Any
from urllib.parse import urlparse

from backend.core.abc.job_import import JobUrlExtractorPort
from backend.core.job_import import ImportStatus, JobImportFields, JobImportResult

logger = logging.getLogger(__name__)


def _to_clean_str(value: Any) -> str | None:
    if value is None or isinstance(value, (bool, dict, list)):
        return None
    if isinstance(value, (str, int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None
    return None


def _to_clean_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool) or isinstance(value, (dict, list)):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        if value.is_integer() and value >= 0:
            return int(value)
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if re.fullmatch(r"^\d+$", cleaned):
            try:
                val = int(cleaned)
                return val if val >= 0 else None
            except ValueError:
                return None
        return None
    return None


class ImportJobPreviewUseCase:
    def __init__(
        self,
        extractor: JobUrlExtractorPort,
    ) -> None:
        self.extractor = extractor

    async def execute(self, url: str) -> JobImportResult:
        url = url.strip()
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                return JobImportResult(
                    status=ImportStatus.UNAVAILABLE,
                    source_url=url,
                    fields=JobImportFields(),
                    reason_code="disallowed_url",
                    message="Invalid URL format",
                )
        except Exception:
            return JobImportResult(
                status=ImportStatus.UNAVAILABLE,
                source_url=url,
                fields=JobImportFields(),
                reason_code="disallowed_url",
                message="Invalid URL format",
            )

        extracted_fields, reason_code, message = await self.extractor.extract_job_fields_from_url(url)
        if not extracted_fields:
            return JobImportResult(
                status=ImportStatus.UNAVAILABLE,
                source_url=url,
                fields=JobImportFields(),
                reason_code=reason_code or "provider_unavailable",
                message=message or "AI URL extraction failed",
            )

        normalized_fields = self._normalize_fields(extracted_fields, url)

        has_title = bool(normalized_fields.title)
        has_company = bool(normalized_fields.company)

        if has_title and has_company:
            status = ImportStatus.COMPLETE
        else:
            status = ImportStatus.PARTIAL

        return JobImportResult(
            status=status,
            source_url=url,
            fields=normalized_fields,
            reason_code=None,
            message=None,
        )

    def _normalize_fields(self, fields: JobImportFields, source_url: str) -> JobImportFields:
        title = _to_clean_str(fields.title)
        company = _to_clean_str(fields.company)
        description = _to_clean_str(fields.description)
        location = _to_clean_str(fields.location)
        source = _to_clean_str(fields.source)
        if source and source.lower().startswith(("http://", "https://")):
            source = urlparse(source_url).hostname

        salary_min = _to_clean_int(fields.salary_min)
        salary_max = _to_clean_int(fields.salary_max)

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            salary_min = None
            salary_max = None

        has_numeric_salary = salary_min is not None or salary_max is not None

        currency = None
        curr_str = _to_clean_str(fields.currency)
        if curr_str:
            curr_clean = curr_str.upper()
            if re.fullmatch(r"^[A-Z]{3}$", curr_clean):
                currency = curr_clean

        salary_period = None
        period_str = _to_clean_str(fields.salary_period)
        if period_str:
            period_clean = period_str.lower()
            if period_clean in ("hour", "month", "year"):
                salary_period = period_clean

        if has_numeric_salary:
            if not currency or not salary_period:
                salary_min = None
                salary_max = None
                currency = None
                salary_period = None

        technologies = None
        if isinstance(fields.technologies, list):
            tech_set = []
            for item in fields.technologies:
                clean_item = _to_clean_str(item)
                if clean_item and clean_item not in tech_set:
                    tech_set.append(clean_item)
            if tech_set:
                technologies = tech_set

        return JobImportFields(
            title=title,
            company=company,
            description=description,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            salary_period=salary_period,
            technologies=technologies,
            source=source,
        )
