from fastapi import APIRouter, Depends

from backend.api.dependencies import require_active_user
from backend.api.schemas.job import JobListResponse, JobResponse
from backend.api.schemas.job_import import ImportPreviewResponse

from .create_job import create_job as create_job_endpoint
from .delete_job import delete_job as delete_job_endpoint
from .get_job import get_job as get_job_endpoint
from .import_job_preview import import_job_preview as import_job_preview_endpoint
from .list_jobs import list_jobs as list_jobs_endpoint
from .update_job import update_job as update_job_endpoint

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_active_user)],
)

router.add_api_route(
    path="",
    methods={"POST"},
    endpoint=create_job_endpoint,
    response_model=JobResponse,
    status_code=201,
)

router.add_api_route(
    path="/import-preview",
    methods={"POST"},
    endpoint=import_job_preview_endpoint,
    response_model=ImportPreviewResponse,
    status_code=200,
)

router.add_api_route(
    path="",
    methods={"GET"},
    endpoint=list_jobs_endpoint,
    response_model=JobListResponse,
    status_code=200,
)

router.add_api_route(
    path="/{job_id}",
    methods={"GET"},
    endpoint=get_job_endpoint,
    response_model=JobResponse,
    status_code=200,
)

router.add_api_route(
    path="/{job_id}",
    methods={"PATCH"},
    endpoint=update_job_endpoint,
    response_model=JobResponse,
    status_code=200,
)

router.add_api_route(
    path="/{job_id}",
    methods={"DELETE"},
    endpoint=delete_job_endpoint,
    status_code=204,
)
