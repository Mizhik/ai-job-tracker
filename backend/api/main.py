from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .container import Container
from .endpoints import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    await container.init_resources()
    yield

    await container.shutdown_resources()


def build_app() -> FastAPI:
    origins = [
        "http://localhost",
    ]

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=("GET", "POST"),
        allow_headers=("*",),
    )

    for prefix, router in (("", ai_router),):
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
