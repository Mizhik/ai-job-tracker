from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from backend.api.dependencies import require_active_user
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.service import JobService
from backend.core.user import User


@inject
async def list_jobs(
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    return await job_service.list_jobs(ListJobsQuery(user_id=current_user.id))
