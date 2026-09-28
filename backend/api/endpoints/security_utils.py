from urllib.parse import urlparse
from fastapi import HTTPException, Request, status


def verify_origin_or_referer(request: Request, allowed_origins: list[str]) -> None:
    origin = request.headers.get("origin")
    if origin:
        cleaned_origin = origin.rstrip("/")
        normalized_allowed = [o.rstrip("/") for o in allowed_origins]
        if cleaned_origin not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Origin not allowed",
            )
        return

    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if not parsed.scheme or not parsed.netloc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Invalid Referer header",
            )
        referer_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        normalized_allowed = [o.rstrip("/") for o in allowed_origins]
        if referer_origin not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Referer origin not allowed",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: Missing Origin and Referer headers",
    )
