# src\fbr\router.py

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException
from src.fbr.schemas import (
    FBRIntegrationRequest,
    FBRIntegrationResponse,
    FBRSubmissionRequest,
    FBRSubmissionResponse,
    FBRUOMRequest,
    FBRUOMResponse,
    FBRValidationRequest,
    FBRValidationResponse,
)
from src.fbr.service import FBRIntegrationService, FBRInvoiceService

router = APIRouter(prefix="/fbr", tags=["FBR"], responses=ERROR_RESPONSES)


@router.post("/invoice/validate", response_model=FBRValidationResponse)
async def fbr_validate_invoice(
    input_data: FBRValidationRequest,
    auth_user: AuthenticatedUser,
) -> FBRValidationResponse:
    """Validate an invoice with the FBR.

    Args:
        input_data: Request payload containing the invoice identifier.
        auth_user: Authenticated user context injected by the dependency layer.

    Returns:
        FBRValidationResponse: Validation result returned by the service layer.
    """

    try:
        return await FBRInvoiceService.validate_invoice(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as exc:  # pragma: no cover - cooperative FastAPI error handling
        raise InternalServerErrorException(
            message="Failed to validate invoice with FBR",
            detail=str(exc),
            extra={
                "operation": "fbr_validate_invoice",
                "user_id": str(auth_user.user.id),
                "invoice_id": str(input_data.invoice_id),
            },
        ) from exc


@router.post("/invoice/submit", response_model=FBRSubmissionResponse)
async def fbr_submit_invoice(
    input_data: FBRSubmissionRequest,
    auth_user: AuthenticatedUser,
) -> FBRSubmissionResponse:
    """Submit an invoice to the FBR.

    Args:
        input_data: Request payload containing the invoice identifier.
        auth_user: Authenticated user context injected by the dependency layer.

    Returns:
        FBRSubmissionResponse: Submission result returned by the service layer.
    """

    try:
        return await FBRInvoiceService.submit_invoice(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as exc:  # pragma: no cover - cooperative FastAPI error handling
        raise InternalServerErrorException(
            message="Failed to submit invoice to FBR",
            detail=str(exc),
            extra={
                "operation": "fbr_submit_invoice",
                "user_id": str(auth_user.user.id),
                "invoice_id": str(input_data.invoice_id),
            },
        ) from exc


@router.get("/uom", response_model=FBRUOMResponse)
async def fbr_get_uom(
    auth_user: AuthenticatedUser, input_params: FBRUOMRequest = Query()
) -> FBRUOMResponse:
    """Retrieve the unit of measurement description from the FBR API.

    Args:
        auth_user: Authenticated user context injected by the dependency layer.
        hs_code: HS code used to query the FBR UOM endpoint.
        annexure_id: Annexure identifier used to refine the search.

    Returns:
        FBRUOMResponse: Parsed response containing the unit of measurement description.
    """

    try:
        return await FBRInvoiceService.get_uom(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as exc:  # pragma: no cover - cooperative FastAPI error handling
        raise InternalServerErrorException(
            message="Failed to retrieve FBR UOM data",
            detail=str(exc),
            extra={
                "operation": "fbr_get_uom",
                "hs_code": input_params.hs_code,
                "annexure_id": input_params.annexure_id,
                "user_id": str(auth_user.user.id),
            },
        ) from exc


@router.post("/integration", response_model=FBRIntegrationResponse)
async def fbr_integration(
    input_data: FBRIntegrationRequest,
    auth_user: AuthenticatedUser,
) -> FBRIntegrationResponse:
    """Execute the FBR sandbox integration test suite.

    Args:
        input_data: Request payload containing the target user and scenarios.
        auth_user: Authenticated user context injected by the dependency layer.

    Returns:
        FBRIntegrationResponse: Aggregated results for each executed scenario.
    """

    try:
        return await FBRIntegrationService.run_integration(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as exc:  # pragma: no cover - cooperative FastAPI error handling
        raise InternalServerErrorException(
            message="Failed to execute FBR integration scenarios",
            detail=str(exc),
            extra={
                "operation": "fbr_run_integration",
                "user_id": str(input_data.user_id or auth_user.user.id),
            },
        ) from exc
