from uuid import UUID

from fastapi import Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.service import JobService
from backend.core.errors import JobNotFoundError


@inject
async def get_job(
    job_id: UUID,
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        return await job_service.get_job_by_id(GetJobByIdQuery(job_id=job_id))
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
