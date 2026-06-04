from typing import AsyncGenerator

from dependency_injector import containers, providers
from asyncpg import Pool

from backend.infrastructure.db import create_pool, DBSettings


async def resource_asyncpg_pool(db_settings: DBSettings) -> AsyncGenerator[Pool, None]:
    pool = await create_pool(db_settings)

    yield pool

    await pool.close()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["backend.api"])

    db_settings = providers.Singleton(DBSettings)
    pool = providers.Resource(resource_asyncpg_pool, db_settings=db_settings)

    
