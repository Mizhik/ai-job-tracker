from fastapi import APIRouter, Depends

from backend.api.dependencies import require_active_user
from backend.api.schemas.application import ApplicationResponse

from .create_application import create_application as create_application_endpoint
from .delete_application import delete_application as delete_application_endpoint
from .get_application import get_application as get_application_endpoint
from .update_application import update_application as update_application_endpoint

router = APIRouter(
    dependencies=[Depends(require_active_user)],
)

router.add_api_route(
    path="/jobs/{job_id}/application",
    methods={"POST"},
    endpoint=create_application_endpoint,
    response_model=ApplicationResponse,
    status_code=201,
    tags=["applications"],
)

router.add_api_route(
    path="/applications/{application_id}",
    methods={"GET"},
    endpoint=get_application_endpoint,
    response_model=ApplicationResponse,
    status_code=200,
    tags=["applications"],
)

router.add_api_route(
    path="/applications/{application_id}",
    methods={"PATCH"},
    endpoint=update_application_endpoint,
    response_model=ApplicationResponse,
    status_code=200,
    tags=["applications"],
)

router.add_api_route(
    path="/applications/{application_id}",
    methods={"DELETE"},
    endpoint=delete_application_endpoint,
    status_code=204,
    tags=["applications"],
)
