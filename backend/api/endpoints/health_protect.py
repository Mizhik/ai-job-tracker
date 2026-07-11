from typing import Annotated

from asyncpg import Pool
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from backend.api.dependencies import require_active_user
from backend.core.user import User


@inject
async def health_check_protected(
    current_user: Annotated[User, Depends(require_active_user)],
    pool: Pool = Depends(Provide["pool"]),
) -> str:
    async with pool.acquire() as connection:
        result = await connection.execute("SELECT 1")

    if current_user.email != "user@example.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return "OK" if result else "Error"
