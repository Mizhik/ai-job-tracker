from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Query, status

from backend.api.dependencies import require_active_user
from backend.app.jobs.queries.list_jobs import ListJobsQuery, ListJobsResult
from backend.app.jobs.service import JobService
from backend.core.user import User

ALLOWED_STATUS_FILTERS = {
    "saved",
    "applied",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
}


@inject
async def list_jobs(
    q: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
) -> ListJobsResult:
    if status_filter is not None and status_filter.strip():
        clean_status = status_filter.strip().lower()
        if clean_status not in ALLOWED_STATUS_FILTERS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status filter: {status_filter}",
            )
        status_param = clean_status
    else:
        status_param = None

    res = await job_service.list_jobs(
        ListJobsQuery(
            user_id=current_user.id,
            q=q,
            status=status_param,
            limit=limit,
            offset=offset,
        )
    )
    return res
