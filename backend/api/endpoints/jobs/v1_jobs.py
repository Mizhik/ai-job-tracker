from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import JSONResponse

from backend.api.dependencies import require_active_user
from backend.api.schemas.job import (
    JobV1CreateInput,
    JobV1ListResponse,
    JobV1Response,
    JobV1UpdateInput,
    V1ErrorResponse,
)
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.queries.list_jobs import ListJobsQuery
from backend.app.jobs.commands.delete_job import DeleteJobCommand
from backend.app.jobs.service import JobService
from backend.core.errors import InvalidJobDataError, JobNotFoundError
from backend.core.user import User

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["v1-jobs"],
    dependencies=[Depends(require_active_user)],
)


@router.post(
    "",
    response_model=JobV1Response,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": V1ErrorResponse}},
)
@inject
async def create_job_v1(
    body: JobV1CreateInput,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        job = await job_service.create_job(body.to_command(current_user.id))
        return job
    except InvalidJobDataError as err:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "validation_error",
                "message": err.detail,
                "details": [],
            },
        )


@router.get(
    "",
    response_model=JobV1ListResponse,
    status_code=status.HTTP_200_OK,
    responses={422: {"model": V1ErrorResponse}},
)
@inject
async def list_jobs_v1(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    res = await job_service.list_jobs_v1(
        ListJobsQuery(
            user_id=current_user.id,
            q=q,
            limit=limit,
            offset=offset,
        )
    )
    return res


@router.get(
    "/{job_id}",
    response_model=JobV1Response,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": V1ErrorResponse}},
)
@inject
async def get_job_v1(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        job = await job_service.get_job_by_id(
            GetJobByIdQuery(job_id=job_id, user_id=current_user.id)
        )
        return job
    except JobNotFoundError as err:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "not_found",
                "message": err.detail,
                "details": [],
            },
        )


@router.patch(
    "/{job_id}",
    response_model=JobV1Response,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": V1ErrorResponse},
        422: {"model": V1ErrorResponse},
    },
)
@inject
async def update_job_v1(
    job_id: UUID,
    body: JobV1UpdateInput,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        job = await job_service.update_job(body.to_command(job_id, current_user.id))
        return job
    except JobNotFoundError as err:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "not_found",
                "message": err.detail,
                "details": [],
            },
        )
    except InvalidJobDataError as err:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "validation_error",
                "message": err.detail,
                "details": [],
            },
        )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": V1ErrorResponse}},
)
@inject
async def delete_job_v1(
    job_id: UUID,
    current_user: User = Depends(require_active_user),
    job_service: JobService = Depends(Provide["job_service"]),
):
    try:
        await job_service.delete_job(
            DeleteJobCommand(job_id=job_id, user_id=current_user.id)
        )
    except JobNotFoundError as err:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "not_found",
                "message": err.detail,
                "details": [],
            },
        )
