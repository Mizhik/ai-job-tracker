from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .container import Container
from .endpoints import router as user_router
from .endpoints.jobs import router as jobs_router
from .endpoints.jobs.v1_jobs import router as v1_jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    app.state.container = container
    await container.init_resources()
    yield

    await container.shutdown_resources()
    del app.state.container


def build_app() -> FastAPI:
    origins = [
        "http://localhost",
    ]

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=("GET", "POST", "PATCH", "DELETE", "OPTIONS"),
        allow_headers=("*",),
    )

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api/v1/"):
            code = "unauthorized" if exc.status_code == 401 else (
                "forbidden" if exc.status_code == 403 else (
                    "not_found" if exc.status_code == 404 else "error"
                )
            )
            message = exc.detail if isinstance(exc.detail, str) else "An error occurred"
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": code,
                    "message": message,
                    "details": [],
                },
                headers=exc.headers,
            )
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
        if request.url.path.startswith("/api/v1/"):
            details = []
            for err in exc.errors():
                details.append({
                    "loc": [str(loc_item) for loc_item in err.get("loc", [])],
                    "msg": str(err.get("msg", "")),
                    "type": str(err.get("type", "")),
                })
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "code": "validation_error",
                    "message": "Invalid request parameter or payload",
                    "details": details,
                },
            )
        return await request_validation_exception_handler(request, exc)

    for prefix, router in (
        ("", user_router),
        ("", jobs_router),
        ("", v1_jobs_router),
    ):
        app.include_router(router=router, prefix=prefix)

    return app


def main():

    os.system(
        "uvicorn "
        "backend.api.main:build_app "
        "--factory "
        f"--host=127.0.0.1 "
        "--port=8000 "
        "--reload "
        "--env-file=dev.env"
    )


if __name__ == "__main__":
    main()
