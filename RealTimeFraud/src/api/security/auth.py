import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    if not settings.require_api_key:
        return "anonymous"

    if not api_key or not secrets.compare_digest(api_key, settings.effective_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Include a valid X-API-Key header.",
        )
    return api_key
