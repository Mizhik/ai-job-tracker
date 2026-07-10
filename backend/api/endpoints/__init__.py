from fastapi import APIRouter

from backend.api.schemas.auth import AccessTokenResponse
from backend.api.schemas.user import UserResponse

from .health import health_check
# from .health_protect import health_check_protected
from .register_user import register_user as register_user_endpoint
from .login import login_for_access_token
from .get_user_by_token import get_user_by_token as get_user_by_token_endpoint
from .update_user import update_user as update_user_endpoint
from .delete_user import delete_user as delete_user_endpoint

router = APIRouter(prefix="/users", tags=["users"])

router.add_api_route(
    path="/health",
    methods={
        "GET",
    },
    endpoint=health_check,
    status_code=200,
)

# router.add_api_route(
#     path="/health-protect",
#     methods={
#         "GET",
#     },
#     endpoint=health_check_protected,
#     status_code=200,
# )

router.add_api_route(
    path="/register",
    methods={
        "POST",
    },
    endpoint=register_user_endpoint,
    response_model=UserResponse,
    status_code=202,
)

router.add_api_route(
    path="/update/{user_id}",
    methods={
        "PUT",
    },
    endpoint=update_user_endpoint,
    response_model=UserResponse,
    status_code=202,
)

router.add_api_route(
    path="/delete/{user_id}",
    methods={
        "DELETE",
    },
    endpoint=delete_user_endpoint,
    status_code=204,
)

router.add_api_route(
    path="/login",
    methods={
        "POST",
    },
    endpoint=login_for_access_token,
    response_model=AccessTokenResponse,
    status_code=200,
)

router.add_api_route(
    path="/me",
    methods={
        "GET",
    },
    endpoint=get_user_by_token_endpoint,
    response_model=UserResponse,
    status_code=200,
)
