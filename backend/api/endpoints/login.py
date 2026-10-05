from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.schemas.auth import AccessTokenResponse, LoginRequest
from backend.app.auth.service import AuthService
from backend.core.errors import EmailOrPasswordIncorrectError, UserBlockedError
from backend.infrastructure.settings.auth import AuthSettings


@inject
async def login_for_access_token(
    response: Response,
    auth_service: AuthService = Depends(Provide["auth_service"]),
    auth_settings: AuthSettings = Depends(Provide["auth_settings"]),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> AccessTokenResponse:
    login_request = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    command = login_request.to_command()
    try:
        login_result = await auth_service.login(command)
    except EmailOrPasswordIncorrectError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserBlockedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.detail)

    if login_result.raw_refresh_token:
        response.set_cookie(
            key=auth_settings.refresh_cookie_name,
            value=login_result.raw_refresh_token,
            httponly=True,
            secure=auth_settings.cookie_secure,
            samesite=auth_settings.cookie_samesite,
            max_age=7 * 24 * 3600,
            path="/users",
        )

    return AccessTokenResponse(
        access_token=login_result.access_token,
        token_type="bearer",
    )
