from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.job import JobUpdateInput
from backend.app.jobs.service import JobService
from backend.core.errors import InvalidJobDataError, JobNotFoundError
from backend.core.job import Job
from backend.core.user import User


@inject
async def update_job(
    job_id: UUID,
    job_update_input: JobUpdateInput,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
) -> Job:
    try:
        job = await job_service.update_job(
            job_update_input.to_command(job_id=job_id, user_id=current_user.id)
        )
        return job
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
    except InvalidJobDataError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail,
        )
