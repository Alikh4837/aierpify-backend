# src\customers\router.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from src.customers.schemas import (
    CreateCustomerRequest,
    CreateCustomerResponse,
    DeleteCustomerRequest,
    DeleteCustomerResponse,
    GetCustomerRequest,
    GetCustomerResponse,
    GetCustomersRequest,
    GetCustomersResponse,
    UpdateCustomerRequest,
    UpdateCustomerResponse,
)
from src.customers.service import CustomerService
from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException

router = APIRouter(prefix="/customers", tags=["Customers"], responses=ERROR_RESPONSES)


# ---------------------------------------------------------------------------- #
#                              Customer Endpoints                              #
# ---------------------------------------------------------------------------- #
@router.get("/{customer_id}", response_model=GetCustomerResponse)
async def get_customer(
    customer_id: UUID,
    auth_user: AuthenticatedUser,
    user_id: Optional[UUID] = Query(default=None),
) -> GetCustomerResponse:
    """List customers with filtering & pagination for the authenticated user."""
    try:
        input_params = GetCustomerRequest(id=customer_id, user_id=user_id)
        return await CustomerService.get_customer_single(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve customer",
            detail=str(e),
            extra={"operation": "get_customer", "user_id": str(auth_user.user.id)},
        )


@router.get("", response_model=GetCustomersResponse)
async def get_customers(
    auth_user: AuthenticatedUser,
    input_params: GetCustomersRequest = Query(),
) -> GetCustomersResponse:
    """List customers with filtering & pagination for the authenticated user."""
    try:
        return await CustomerService.get_customers(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve customers",
            detail=str(e),
            extra={"operation": "get_customers", "user_id": str(auth_user.user.id)},
        )


@router.post("", response_model=CreateCustomerResponse)
async def create_customer(
    input_data: CreateCustomerRequest, auth_user: AuthenticatedUser
) -> CreateCustomerResponse:
    """Create a new customer."""
    try:
        return await CustomerService.create_customer(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create customer",
            detail=str(e),
            extra={"operation": "create_customer", "user_id": str(auth_user.user.id)},
        )


@router.patch("", response_model=UpdateCustomerResponse)
async def update_customer(
    input_data: UpdateCustomerRequest,
    auth_user: AuthenticatedUser,
) -> UpdateCustomerResponse:
    """Update an existing customer."""
    try:
        return await CustomerService.update_customer(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update customer",
            detail=str(e),
            extra={
                "operation": "update_customer",
                "user_id": str(auth_user.user.id),
            },
        )


@router.delete("", response_model=DeleteCustomerResponse)
async def delete_customers(
    input_data: DeleteCustomerRequest, auth_user: AuthenticatedUser
) -> DeleteCustomerResponse:
    """Bulk delete customers by IDs."""
    try:
        return await CustomerService.delete_customers(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to bulk delete customers",
            detail=str(e),
            extra={
                "operation": "delete_customers",
                "user_id": str(auth_user.user.id),
            },
        )
