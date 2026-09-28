from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.infrastructure.settings.auth import AuthSettings
from .container import Container
from .endpoints import router as user_router
from .endpoints.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    app.state.container = container
    await container.init_resources()
    yield

    await container.shutdown_resources()
    del app.state.container


def get_allowed_origins() -> list[str]:
    try:
        settings = AuthSettings()
        origins = settings.allowed_origins
        return origins if isinstance(origins, list) else [origins]
    except Exception:
        return [
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]


def build_app() -> FastAPI:
    origins = get_allowed_origins()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=("GET", "POST", "PATCH", "DELETE", "OPTIONS"),
        allow_headers=("*",),
    )

    for prefix, router in (
        ("", user_router),
        ("", jobs_router),
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
