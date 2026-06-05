from asyncpg import Pool, create_pool as create_asyncpg_pool

from backend.infrastructure.postgres.pool.settings import DBSettings


async def create_pool(settings: DBSettings) -> Pool:
    pool = await create_asyncpg_pool(dsn=settings.get_url())

    return pool
