from typing import AsyncGenerator

from dependency_injector import containers, providers
from asyncpg import Pool
from fastapi.security import OAuth2PasswordBearer

from backend.api.dependencies import ActiveUserDependency, CurrentUserDependency
from backend.app.auth.service import AuthService
from backend.app.users.service import UserService
from backend.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from backend.infrastructure.postgres import create_pool, DBSettings
from backend.infrastructure.postgres.user_repository import AsyncpgUserRepository
from backend.infrastructure.settings.auth import AuthSettings
from backend.infrastructure.token.jwt_token_service import JwtTokenService


async def resource_asyncpg_pool(db_settings: DBSettings) -> AsyncGenerator[Pool, None]:
    pool = await create_pool(db_settings)

    yield pool

    await pool.close()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["backend.api"])

    db_settings = providers.Singleton(DBSettings)
    auth_settings = providers.Singleton(AuthSettings)
    pool = providers.Resource(resource_asyncpg_pool, db_settings=db_settings)

    user_repository = providers.Singleton(AsyncpgUserRepository, pool)
    password_hasher = providers.Singleton(Argon2PasswordHasher)
    jwt_token_service = providers.Singleton(
        JwtTokenService,
        settings=auth_settings,
    )
    oauth2_scheme = providers.Singleton(
        OAuth2PasswordBearer,
        tokenUrl="/token",
        auto_error=False,
    )

    user_service = providers.Singleton(
        UserService,
        user_repository=user_repository,
        password_hasher=password_hasher,
    )

    auth_service = providers.Singleton(
        AuthService,
        user_repository=user_repository,
        auth_settings=auth_settings,
        access_token_generator=jwt_token_service,
        password_hasher=password_hasher,
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
