import time
from collections import defaultdict
from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from backend.api.dependencies import require_active_user
from backend.api.schemas.job_import import (
    ImportPreviewRequest,
    ImportPreviewResponse,
    JobImportFieldsSchema,
)
from backend.app.jobs.commands.import_job_preview import ImportJobPreviewUseCase
from backend.core.user import User

_USER_REQUEST_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60.0


def _check_rate_limit(user_id_str: str) -> bool:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = [t for t in _USER_REQUEST_TIMESTAMPS[user_id_str] if t > cutoff]
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        _USER_REQUEST_TIMESTAMPS[user_id_str] = timestamps
        return False
    timestamps.append(now)
    _USER_REQUEST_TIMESTAMPS[user_id_str] = timestamps
    return True


@inject
async def import_job_preview(
    request: ImportPreviewRequest,
    current_user: User = Depends(require_active_user),
    import_job_preview_use_case: ImportJobPreviewUseCase = Depends(
        Provide["import_job_preview_use_case"]
    ),
) -> ImportPreviewResponse:
    url_str = str(request.url)

    if not _check_rate_limit(str(current_user.id)):
        return ImportPreviewResponse(
            status="unavailable",
            source_url=url_str,
            fields=JobImportFieldsSchema(),
            reason_code="rate_limit_exceeded",
            message="Rate limit exceeded. Please wait before trying again.",
        )

    result = await import_job_preview_use_case.execute(url_str)

    fields_schema = JobImportFieldsSchema(
        title=result.fields.title,
        company=result.fields.company,
        description=result.fields.description,
        location=result.fields.location,
        salary_min=result.fields.salary_min,
        salary_max=result.fields.salary_max,
        currency=result.fields.currency,
        salary_period=result.fields.salary_period if result.fields.salary_period in ("hour", "month", "year") else None,
        technologies=result.fields.technologies,
        source=result.fields.source,
    )

    return ImportPreviewResponse(
        status=result.status.value if hasattr(result.status, "value") else str(result.status),
        source_url=result.source_url,
        fields=fields_schema,
        reason_code=result.reason_code,
        message=result.message,
    )
