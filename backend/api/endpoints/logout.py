from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, Request, Response, status

from backend.api.endpoints.security_utils import verify_origin_or_referer
from backend.app.auth.commands.logout import LogoutCommand
from backend.app.auth.service import AuthService
from backend.core.errors import TokenInvalidError
from backend.infrastructure.settings.auth import AuthSettings


@inject
async def logout_user(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(Provide["auth_service"]),
    auth_settings: AuthSettings = Depends(Provide["auth_settings"]),
):
    allowed_origins = (
        auth_settings.allowed_origins
        if isinstance(auth_settings.allowed_origins, list)
        else [auth_settings.allowed_origins]
    )
    verify_origin_or_referer(request, allowed_origins)

    raw_cookie = request.cookies.get(auth_settings.refresh_cookie_name)
    csrf_token = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token") or ""

    if raw_cookie:
        if not csrf_token:
            response.delete_cookie(
                key=auth_settings.refresh_cookie_name,
                path="/users",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing CSRF token header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        command = LogoutCommand(
            raw_refresh_token=raw_cookie,
            csrf_token=csrf_token,
            secret_key=auth_settings.secret_key,
        )
        try:
            await auth_service.logout(command)
        except TokenInvalidError as err:
            response.delete_cookie(
                key=auth_settings.refresh_cookie_name,
                path="/users",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=err.detail,
                headers={"WWW-Authenticate": "Bearer"},
            )

    response.delete_cookie(
        key=auth_settings.refresh_cookie_name,
        path="/users",
    )
    return {"message": "Logged out successfully"}
