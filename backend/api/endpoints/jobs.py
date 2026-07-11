from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from backend.api.container import Container
from backend.api.schemas.job import JobCreate, JobResponse
from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery
from backend.app.jobs.service import JobService
from backend.core.errors import JobNotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_job(
    job_create: JobCreate,
    job_service: JobService = Depends(Provide[Container.job_service]),
):
    command = CreateJobCommand(**job_create.model_dump())
    return await job_service.create_job(command)


@router.get("", response_model=list[JobResponse])
@inject
async def list_jobs(
    job_service: JobService = Depends(Provide[Container.job_service]),
):
    return await job_service.list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
@inject
async def get_job(
    job_id: UUID,
    job_service: JobService = Depends(Provide[Container.job_service]),
):
    try:
        return await job_service.get_job_by_id(GetJobByIdQuery(job_id=job_id))
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
