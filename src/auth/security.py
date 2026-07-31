# src\auth\security.py

from fastapi import Cookie
from fastapi.security import APIKeyHeader, HTTPBearer

from src.config import get_setting

# -------------------------- Security Schemes -------------------------- #
AuthorizationHeader: HTTPBearer = HTTPBearer(
    description="Authorization header with JWT token for the user.",
    auto_error=False,
)
APIHeader: APIKeyHeader = APIKeyHeader(
    name="X-API-KEY", description="X-API-Key header for the user.", auto_error=False
)
SessionCookie = Cookie(
    alias=get_setting(
        "BETTER_AUTH_SESSION_COOKIE_ALIAS", "__Secure-aierpify.session_token"
    ),
    description="Session cookie for the user.",
)
