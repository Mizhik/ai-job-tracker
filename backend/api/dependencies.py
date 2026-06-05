from typing import NoReturn

from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.app.auth.queries.get_user_by_token import GetUserByTokenQuery
from backend.app.auth.service import AuthService
from backend.core.errors import TokenInvalidError, TokenIsExpiredError, UserNotFoundError
from backend.core.user import User


class CurrentUserDependency:

    def __init__(
        self,
        auth_service: AuthService,
        oauth2_scheme: OAuth2PasswordBearer,
    ):
        self._auth_service = auth_service
        self._oauth2_scheme = oauth2_scheme

    async def __call__(self, request: Request) -> User | None:
        token = await self._oauth2_scheme(request)

        if not token:
            return None

        try:
            user = await self._auth_service.get_user_by_token(
                GetUserByTokenQuery(token=token)
            )
        except (
            JWTError,
            TokenInvalidError,
            TokenIsExpiredError,
            UserNotFoundError,
        ) as err:
            detail = err.default_detail if hasattr(err, "default_detail") else str(err)
            self.__raise_credentials_exception(detail)

        return user

    def __raise_credentials_exception(self, err: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ActiveUserDependency:
    def __init__(self, get_current_user: CurrentUserDependency):
        self._get_current_user = get_current_user

    async def __call__(self, request: Request) -> User:
        current_user = await self._get_current_user(request)

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if current_user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not active",
            )

        return current_user


async def get_current_user(request: Request) -> User | None:
    container = request.app.state.container
    dependency = await container.get_current_user()
    return await dependency(request)


async def require_active_user(request: Request) -> User:
    container = request.app.state.container
    dependency = await container.require_active_user()
    return await dependency(request)
