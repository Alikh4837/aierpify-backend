# src\stats\router.py

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException
from src.stats.schemas import GetInvoiceStatsRequest, GetInvoiceStatsResponse
from src.stats.service import StatsService

router = APIRouter(prefix="/stats", tags=["Statistics"], responses=ERROR_RESPONSES)


@router.get(
    "/invoices",
    response_model=GetInvoiceStatsResponse,
    tags=["Products", "Invoices", "Customers"],
)
async def get_invoice_stats(
    auth_user: AuthenticatedUser,
    input_data: GetInvoiceStatsRequest = Query(),
) -> GetInvoiceStatsResponse:
    """Fetch quarterly invoice statistics for the authenticated user."""
    try:
        stats = await StatsService.get_invoice_stats(auth_user, input_data)

        return GetInvoiceStatsResponse(**stats.model_dump())

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve invoice statistics",
            detail=str(e),
            extra={"operation": "get_invoice_stats", "user_id": str(auth_user.user.id)},
        )
