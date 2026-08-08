from fastapi import HTTPException, Request

from app.core.config import get_settings

settings = get_settings()


def authenticate_api_key(request: Request) -> None:
    api_key = request.headers.get("x-api-key")

    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
