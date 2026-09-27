from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.api.schemas.job import JobCreateInput
from backend.app.jobs.service import JobService
from backend.core.errors import InvalidJobDataError
from backend.core.user import User


@inject
async def create_job(
    job_create_input: JobCreateInput,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        return await job_service.create_job(job_create_input.to_command(current_user.id))
    except InvalidJobDataError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.detail,
        )
