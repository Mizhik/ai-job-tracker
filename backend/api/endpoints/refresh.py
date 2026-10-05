from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, Request, Response, status

from backend.api.endpoints.security_utils import verify_origin_or_referer
from backend.api.schemas.auth import AccessTokenResponse
from backend.app.auth.commands.refresh_token import RefreshTokenCommand
from backend.app.auth.service import AuthService
from backend.core.errors import TokenInvalidError, UserBlockedError, UserNotFoundError
from backend.infrastructure.settings.auth import AuthSettings


@inject
async def refresh_access_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(Provide["auth_service"]),
    auth_settings: AuthSettings = Depends(Provide["auth_settings"]),
) -> AccessTokenResponse:
    allowed_origins = (
        auth_settings.allowed_origins
        if isinstance(auth_settings.allowed_origins, list)
        else [auth_settings.allowed_origins]
    )
    verify_origin_or_referer(request, allowed_origins)

    raw_cookie = request.cookies.get(auth_settings.refresh_cookie_name)
    if not raw_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )

    csrf_token = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token") or ""
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing CSRF token header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    command = RefreshTokenCommand(
        raw_refresh_token=raw_cookie,
        csrf_token=csrf_token,
        secret_key=auth_settings.secret_key,
    )

    try:
        refresh_result = await auth_service.refresh_token(command)
    except (TokenInvalidError, UserNotFoundError) as err:
        detail = getattr(err, "detail", str(err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserBlockedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.detail,
        )

    response.set_cookie(
        key=auth_settings.refresh_cookie_name,
        value=refresh_result.raw_refresh_token,
        httponly=True,
        secure=auth_settings.cookie_secure,
        samesite=auth_settings.cookie_samesite,
        max_age=7 * 24 * 3600,
        path="/users",
    )

    return AccessTokenResponse(
        access_token=refresh_result.access_token,
        token_type="bearer",
    )
