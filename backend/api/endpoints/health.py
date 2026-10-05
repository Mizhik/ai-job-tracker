from asyncpg import Pool
from dependency_injector.wiring import Provide, inject
from fastapi import Depends


@inject
async def health_check(pool: Pool = Depends(Provide["pool"])) -> str:
    async with pool.acquire() as connection:
        result = await connection.execute("SELECT 1")

    return "OK" if result else "Error"
