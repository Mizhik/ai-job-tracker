from typing import AsyncGenerator

from dependency_injector import containers, providers
from asyncpg import Pool

from backend.api.dependencies import ActiveUserDependency, CurrentUserDependency, oauth2_scheme
from backend.app.applications.service import ApplicationService
from backend.app.auth.service import AuthService
from backend.app.jobs.commands.import_job_preview import ImportJobPreviewUseCase
from backend.app.jobs.service import JobService
from backend.app.users.service import UserService
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.gemini_client import GeminiClient
from backend.infrastructure.postgres import create_pool, DBSettings
from backend.infrastructure.postgres.application_repository import AsyncpgApplicationRepository
from backend.infrastructure.postgres.job_repository import AsyncpgJobRepository
from backend.infrastructure.postgres.user_repository import AsyncpgUserRepository
from backend.infrastructure.postgres.user_session_repository import AsyncpgUserSessionRepository
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.settings.gemini import GeminiSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService
from backend.infrastructure.token.session_token_service import DefaultSessionTokenService


async def resource_asyncpg_pool(db_settings: DBSettings) -> AsyncGenerator[Pool, None]:
    pool = await create_pool(db_settings)
    try:
        yield pool
    finally:
        await pool.close()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["backend.api"])

    db_settings = providers.Singleton(DBSettings)
    auth_settings = providers.Singleton(AuthSettings)
    gemini_settings = providers.Singleton(GeminiSettings)
    pool = providers.Resource(resource_asyncpg_pool, db_settings=db_settings)

    user_repository = providers.Singleton(AsyncpgUserRepository, pool)
    user_session_repository = providers.Singleton(AsyncpgUserSessionRepository, pool)
    job_repository = providers.Singleton(AsyncpgJobRepository, pool)
    application_repository = providers.Singleton(AsyncpgApplicationRepository, pool)
    password_hasher = providers.Singleton(Argon2PasswordHasher)
    jwt_token_service = providers.Singleton(
        JwtTokenService,
        settings=auth_settings,
    )
    session_token_service = providers.Singleton(DefaultSessionTokenService)
    oauth2_scheme = providers.Object(oauth2_scheme)

    job_url_extractor = providers.Singleton(
        GeminiClient,
        settings=gemini_settings,
    )

    import_job_preview_use_case = providers.Singleton(
        ImportJobPreviewUseCase,
        extractor=job_url_extractor,
    )

    user_service = providers.Singleton(
        UserService,
        user_repository=user_repository,
        password_hasher=password_hasher,
    )

    job_service = providers.Singleton(
        JobService,
        job_repository=job_repository,
    )

    application_service = providers.Singleton(
        ApplicationService,
        application_repository=application_repository,
        job_repository=job_repository,
    )

    auth_service = providers.Singleton(
        AuthService,
        user_repository=user_repository,
        password_hasher=password_hasher,
        access_token_generator=jwt_token_service,
        user_session_repository=user_session_repository,
        session_token_service=session_token_service,
        access_token_expire_delta=auth_settings.provided.access_token_expire_delta,
    )

    get_current_user = providers.Singleton(
        CurrentUserDependency,
        auth_service=auth_service,
        oauth2_scheme=oauth2_scheme,
    )
    require_active_user = providers.Singleton(
        ActiveUserDependency,
        get_current_user=get_current_user,
    )
