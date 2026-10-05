from datetime import datetime, timezone
from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, Request, status

from backend.core.abc.session_token_service import SessionTokenService
from backend.core.repository.user_session_repository import UserSessionRepository
from backend.infrastructure.settings.auth import AuthSettings


@inject
async def get_csrf_token(
    request: Request,
    auth_settings: AuthSettings = Depends(Provide["auth_settings"]),
    user_session_repository: UserSessionRepository = Depends(
        Provide["user_session_repository"]
    ),
    session_token_service: SessionTokenService = Depends(
        Provide["session_token_service"]
    ),
):
    raw_cookie = request.cookies.get(auth_settings.refresh_cookie_name)
    if not raw_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: missing refresh token cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_id, _ = session_token_service.parse_refresh_token(raw_cookie)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session = await user_session_repository.get_by_id(session_id)
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is revoked or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = session_token_service.hash_token(raw_cookie)
    if session.refresh_token_hash != token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or stale refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    csrf_token = session_token_service.generate_csrf_token(
        session_id=session_id,
        secret_key=auth_settings.secret_key,
    )
    return {"csrf_token": csrf_token}
