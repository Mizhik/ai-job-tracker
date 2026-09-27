from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query

from backend.api.dependencies import require_active_user
from backend.app.jobs.queries.list_jobs import ListJobsQuery, ListJobsResult
from backend.app.jobs.service import JobService
from backend.core.user import User


@inject
async def list_jobs(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
) -> ListJobsResult:
    res = await job_service.list_jobs(
        ListJobsQuery(
            user_id=current_user.id,
            q=q,
            limit=limit,
            offset=offset,
        )
    )
    return res
