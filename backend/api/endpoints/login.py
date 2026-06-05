from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.schemas.auth import AccessTokenResponse, LoginRequest
from backend.app.auth.service import AuthService
from backend.core.errors import EmailOrPasswordIncorrectError, UserBlockedError


@inject
async def login_for_access_token(
    auth_service: AuthService = Depends(Provide["auth_service"]),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> AccessTokenResponse:
    login_request = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    command = login_request.to_command()
    try:
        access_token = await auth_service.login(command)
    except EmailOrPasswordIncorrectError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserBlockedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.detail)

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
