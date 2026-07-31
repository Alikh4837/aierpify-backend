# src\main.py
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.jwt import JWTValidator
from src.auth.utils import get_jwks_data
from src.config import get_setting, settings
from src.customers.router import router as customers_router
from src.exceptions import (
    BaseHTTPException,
    InternalServerErrorException,
    UnprocessableContentException,
)
from src.fbr.router import router as fbr_router
from src.invoices.router import router as invoices_router
from src.products.router import hs_code_router as hs_code_router
from src.products.router import products_router as products_router
from src.stats.router import router as stats_router
from src.users.router import router as users_router

logger = logging.getLogger("fastapi_cli.cli")


# ---------------------------------------------------------------------------- #
#                             App State / Lifespan                             #
# ---------------------------------------------------------------------------- #
# Define the lifespan state type
class State(TypedDict):
    jwt_validator: JWTValidator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    """
    Application lifespan manager that initializes shared resources.

    This function runs at startup to fetch and cache JWKS data for JWT validation,
    eliminating the need to contact the auth server on every request.
    """

    try:
        # Create the JWT validator with cached JWKS
        jwt_validator = JWTValidator(jwks_data=get_jwks_data())

        logger.info("JWKS data fetched and JWTValidator initialized.")

        # Yield the state to be used throughout the application lifecycle
        yield {"jwt_validator": jwt_validator}

    except Exception as e:
        logger.exception("Failed to initialize application lifespan", exc_info=e)
        raise e  # Reraise to prevent app from starting if initialization fails


# ---------------------------------------------------------------------------- #
#                              App Initialization                              #
# ---------------------------------------------------------------------------- #
def custom_generate_unique_id(route: APIRoute):
    return f"{route.name}"


# Create FastAPI app
app = FastAPI(
    title=settings.get("TITLE", "FastAPI App"),
    description=settings.get("DESCRIPTION", "A FastAPI application."),
    version=settings.get("VERSION", "1.0.0"),
    openapi_url=settings.get("OPENAPI_URL", "/openapi.json"),
    docs_url=settings.get("DOCS_URL", "/docs"),
    redoc_url=settings.get("REDOC_URL", "/redoc"),
    default_response_class=JSONResponse,
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------- #
#                              Exception Handling                              #
# -------- This ensures all exceptions conform to our standard format. ------- #
# ---------------------------------------------------------------------------- #
# --------------------- Pydantic Validation Error Handler -------------------- #
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Handles all FastAPI request validation errors (body/query/path).
    Returns ErrorResponse directly (not nested under 'detail').
    """
    exception = UnprocessableContentException(
        message="Request validation failed",
        detail=str(exc.errors()),
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=exception.error_response.model_dump(exclude_none=True),
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    """
    Handles framework-level HTTP errors (404, 405, etc).
    Returns ErrorResponse directly (not nested under 'detail').
    """
    exception = BaseHTTPException(
        status_code=exc.status_code,
        message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=exception.error_response.model_dump(exclude_none=True),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    """
    Ensures all HTTPExceptions return ErrorResponse directly (not nested).
    """
    # If it's our exception, return the error_response directly
    if isinstance(exc, BaseHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.error_response.model_dump(exclude_none=True),
        )

    # Otherwise wrap it in our validated structure
    exception = BaseHTTPException(
        status_code=exc.status_code,
        message="HTTP error",
        detail=str(exc.detail) if exc.detail else None,
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=exception.error_response.model_dump(exclude_none=True),
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError,
):
    """
    Handles Pydantic validation errors that may occur during processing.
    Returns ErrorResponse directly (not nested under 'detail').
    """
    exception = UnprocessableContentException(
        message="Data validation failed",
        detail="Pydantic validation error",
        extra={
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=exception.error_response.model_dump(exclude_none=True),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Catch-all fallback for uncaught exceptions.
    Returns ErrorResponse directly (not nested under 'detail').
    """
    exception = InternalServerErrorException(
        message="Internal server error",
        detail=str(exc),
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=exception.status_code,
        content=exception.error_response.model_dump(exclude_none=True),
    )


# ---------------------------------------------------------------------------- #
#                          Middleware Instrumentation                          #
# ---------------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,  # type: ignore [invalid-argument-type]
    allow_origins=get_setting(
        "ALLOWED_ORIGINS", ["http://localhost:5173", "http://localhost:4173"]
    ),  # Allows origins
    allow_credentials=True,  # Allow credentials cookies
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


class PreflightCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = await call_next(request)
            # 🧠 Tell the browser to cache the preflight response for 10 minutes
            response.headers["Access-Control-Max-Age"] = "600"
            return response
        return await call_next(request)


app.add_middleware(PreflightCacheMiddleware)  # type: ignore [invalid-argument-type]

# ---------------------------------------------------------------------------- #
#                                    Routers                                   #
# ---------------------------------------------------------------------------- #
# Include Routers
app.include_router(users_router)
app.include_router(products_router)
app.include_router(customers_router)
app.include_router(invoices_router)
app.include_router(hs_code_router)
app.include_router(fbr_router)
app.include_router(stats_router)

# Load Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Status Page
@app.get(
    "/",
    summary="Get Status Page",
    description="Returns the status page with the current status of various services.",
    tags=["System"],
    response_class=HTMLResponse,
)
async def status(request: Request):
    """
    Get Status Page

    Returns the status page with the current status of various services.

    - **request**: The request object.
    - **api_status**: The status of the API.
    - **website_status**: The status of the website.
    - **db_status**: The status of the database.
    - **login_status**: The status of the login service.
    - **last_updated**: The last updated time of the status.

    Returns a Jinja2 template response with the status information.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "api_status": "Operational",
            "ml_status": "Operational",
            "db_status": "Operational",
            "auth_status": "Operational",
            "last_updated": "Just Now",
        },
    )


@app.get(
    "/reference",
    summary="Get API Reference Page",
    tags=["System"],
    response_class=HTMLResponse,
)
async def reference(request: Request):
    return templates.TemplateResponse(request, "reference.html", {"request": request})


@app.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the application.",
    tags=["System"],
    response_class=JSONResponse,
)
async def health() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
