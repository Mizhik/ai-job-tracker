from fastapi import APIRouter

from .health import health_check


router = APIRouter()

router.add_api_route(
    path="/health",
    methods={
        "GET",
    },
    endpoint=health_check,
    status_code=200,
)
