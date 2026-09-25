from fastapi import APIRouter, Depends

from backend.api.dependencies import require_active_user

from .create_job import create_job as create_job_endpoint
from .list_jobs import list_jobs as list_jobs_endpoint
from .get_job import get_job as get_job_endpoint
from backend.api.schemas.job import JobResponse

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_active_user)],
)

router.add_api_route(
    path="",
    methods={
        "POST",
    },
    endpoint=create_job_endpoint,
    response_model=JobResponse,
    status_code=201,
)

router.add_api_route(
    path="",
    methods={
        "GET",
    },
    endpoint=list_jobs_endpoint,
    response_model=list[JobResponse],
    status_code=200,
)

router.add_api_route(
    path="/{job_id}",
    methods={
        "GET",
    },
    endpoint=get_job_endpoint,
    response_model=JobResponse,
    status_code=200,
)
