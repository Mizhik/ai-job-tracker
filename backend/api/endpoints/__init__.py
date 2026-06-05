from fastapi import APIRouter

from backend.api.schemas.auth import AccessTokenResponse
from backend.api.schemas.user import UserResponse

from .health import health_check
from .health_protect import health_check_protected
from .register_user import register_user as register_user_endpoint
from .login import login_for_access_token

router = APIRouter()

router.add_api_route(
    path="/health",
    methods={
        "GET",
    },
    endpoint=health_check,
    status_code=200,
)

router.add_api_route(
    path="/health-protect",
    methods={
        "GET",
    },
    endpoint=health_check_protected,
    status_code=200,
)

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
    path="/token",
    methods={
        "POST",
    },
    endpoint=login_for_access_token,
    response_model=AccessTokenResponse,
    status_code=200,
)
