from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.service import JobService
from backend.core.errors import JobNotFoundError
from backend.core.job import Job
from backend.core.user import User


@inject
async def get_job(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
) -> Job:
    try:
        return await job_service.get_job_by_id(
            GetJobByIdQuery(job_id=job_id, user_id=current_user.id)
        )
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
