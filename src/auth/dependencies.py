# src\auth\dependencies.py
from typing import Annotated, Optional, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from src.auth.jwt import JWTValidator
from src.auth.security import APIHeader, AuthorizationHeader, SessionCookie


# --------------------------- Dependency Functions --------------------------- #
def get_jwt_validator(request: Request) -> JWTValidator:
    """
    Dependency to retrieve the cached JWT validator from lifespan state.

    Args:
        request: The FastAPI request object

    Returns:
        JWTValidator: The cached JWT validator instance
    """
    return cast(JWTValidator, request.state.jwt_validator)


# -------------------------- Dependency Annotations -------------------------- #
# Authorization Header Dependency
AuthHeaderDep = Annotated[HTTPAuthorizationCredentials, Depends(AuthorizationHeader)]
# API-Key Header Dependency
APIKeyDep = Annotated[str, Depends(APIHeader)]
# Session Cookie Dependency
SessionCookieDep = Annotated[Optional[str], SessionCookie]
# JWT Validator Dependency
JWTValidatorDep = Annotated[JWTValidator, Depends(get_jwt_validator)]
