# src/exceptions.py
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


# ---------------------------------------------------------------------------- #
#                            Pydantic Error Models                             #
# ---------------------------------------------------------------------------- #
class ErrorResponse(BaseModel):
    """
    Standardized error response structure validated by Pydantic.
    """

    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    detail: Optional[str] = Field(None, description="Additional error details")
    extra: Optional[Dict[str, Any]] = Field(
        None, description="Extra context information"
    )


# ---------------------------------------------------------------------------- #
#                          Base HTTP Exception Class                           #
# ---------------------------------------------------------------------------- #
class BaseHTTPException(HTTPException):
    """
    Base exception for standardized HTTP errors with Pydantic validation.
    Returns the ErrorResponse directly, not nested under 'detail'.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        # Create and validate the error response using Pydantic
        self.error_response = ErrorResponse(
            message=message,
            code=code or str(status_code),
            detail=detail,
            extra=extra,
        )

        # Store status code and serialized response
        self.status_code = status_code
        # Don't pass detail to HTTPException - we'll handle serialization ourselves
        super().__init__(status_code=status_code)


# ---------------------------------------------------------------------------- #
#                           Common HTTP Exceptions                             #
# ---------------------------------------------------------------------------- #
class BadRequestException(BaseHTTPException):
    """Bad Request (400) exception."""

    def __init__(
        self,
        message: str = "Bad Request",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_400_BAD_REQUEST,
            message,
            code=code or "BAD_REQUEST",
            detail=detail,
            extra=extra,
        )


class UnauthorizedException(BaseHTTPException):
    """Unauthorized (401) exception."""

    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_401_UNAUTHORIZED,
            message,
            code=code or "UNAUTHORIZED",
            detail=detail,
            extra=extra,
        )


class ForbiddenException(BaseHTTPException):
    """Forbidden (403) exception."""

    def __init__(
        self,
        message: str = "Forbidden",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_403_FORBIDDEN,
            message,
            code=code or "FORBIDDEN",
            detail=detail,
            extra=extra,
        )


class NotFoundException(BaseHTTPException):
    """Not Found (404) exception."""

    def __init__(
        self,
        message: str = "Not Found",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_404_NOT_FOUND,
            message,
            code=code or "NOT_FOUND",
            detail=detail,
            extra=extra,
        )


class ConflictException(BaseHTTPException):
    """Conflict (409) exception."""

    def __init__(
        self,
        message: str = "Conflict",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_409_CONFLICT,
            message,
            code=code or "CONFLICT",
            detail=detail,
            extra=extra,
        )


class UnprocessableContentException(BaseHTTPException):
    """Unprocessable Content (422) exception."""

    def __init__(
        self,
        message: str = "Unprocessable Content",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_422_UNPROCESSABLE_CONTENT,
            message,
            code=code or "UNPROCESSABLE_CONTENT",
            detail=detail,
            extra=extra,
        )


class InternalServerErrorException(BaseHTTPException):
    """Internal Server Error (500) exception."""

    def __init__(
        self,
        message: str = "Internal Server Error",
        *,
        code: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            code=code or "INTERNAL_SERVER_ERROR",
            detail=detail,
            extra=extra,
        )


# ---------------------------------------------------------------------------- #
#                      OpenAPI Response Documentation                          #
# ---------------------------------------------------------------------------- #

# Standard error responses for use in FastAPI route decorators
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "Bad Request - Invalid input data",
    },
    401: {
        "model": ErrorResponse,
        "description": "Unauthorized - Authentication required",
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden - Insufficient permissions",
    },
    404: {
        "model": ErrorResponse,
        "description": "Not Found - Resource does not exist",
    },
    409: {
        "model": ErrorResponse,
        "description": "Conflict - Resource already exists",
    },
    422: {
        "model": ErrorResponse,
        "description": "Unprocessable Entity - Validation error",
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal Server Error",
    },
}
