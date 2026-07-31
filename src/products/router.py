# src\products\router.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException
from src.products.schemas import (
    CreateHSCodeRequest,
    CreateHSCodeResponse,
    CreateProductRequest,
    CreateProductResponse,
    DeleteHSCodeRequest,
    DeleteHSCodeResponse,
    DeleteProductRequest,
    DeleteProductResponse,
    GetHsCodeRequest,
    GetHsCodeResponse,
    GetHSCodesRequest,
    GetHSCodesResponse,
    GetProductRequest,
    GetProductResponse,
    GetProductsRequest,
    GetProductsResponse,
    UpdateHSCodeRequest,
    UpdateHSCodeResponse,
    UpdateProductRequest,
    UpdateProductResponse,
)
from src.products.service import HSCodeService, ProductService

products_router = APIRouter(tags=["Products"], responses=ERROR_RESPONSES)
hs_code_router = APIRouter(tags=["HS Codes"], responses=ERROR_RESPONSES)


# --------------------------------------------------------------------------- #
#                              Product Endpoints                              #
# --------------------------------------------------------------------------- #
@products_router.get("/products/{product_id}", response_model=GetProductResponse)
async def get_product(
    product_id: UUID,
    auth_user: AuthenticatedUser,
    user_id: Optional[UUID] = Query(default=None),
) -> GetProductResponse:
    """Retrieve a single product by ID for the authenticated user."""
    try:
        input_params = GetProductRequest(id=product_id, user_id=user_id)
        return await ProductService.get_product_single(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve product",
            detail=str(e),
            extra={
                "operation": "get_product",
                "user_id": str(auth_user.user.id),
                "product_id": str(product_id),
            },
        )


@products_router.get("/products", response_model=GetProductsResponse)
async def get_products(
    auth_user: AuthenticatedUser,
    input_params: GetProductsRequest = Query(),
) -> GetProductsResponse:
    """List products with filtering & pagination for the authenticated user."""
    try:
        return await ProductService.get_products(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve products",
            detail=str(e),
            extra={"operation": "list_products", "user_id": str(auth_user.user.id)},
        )


@products_router.post("/products", response_model=CreateProductResponse)
async def create_product(
    input_data: CreateProductRequest, auth_user: AuthenticatedUser
) -> CreateProductResponse:
    """Create a new product."""
    try:
        return await ProductService.create_product(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create product",
            detail=str(e),
            extra={"operation": "create_product", "user_id": str(auth_user.user.id)},
        )


@products_router.patch("/products", response_model=UpdateProductResponse)
async def update_product(
    input_data: UpdateProductRequest,
    auth_user: AuthenticatedUser,
) -> UpdateProductResponse:
    """Update an existing product."""
    try:
        return await ProductService.update_product(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update product",
            detail=str(e),
            extra={
                "operation": "update_product",
                "user_id": str(auth_user.user.id),
            },
        )


@products_router.delete("/products", response_model=DeleteProductResponse)
async def delete_products(
    input_data: DeleteProductRequest, auth_user: AuthenticatedUser
) -> DeleteProductResponse:
    """Bulk delete products by IDs."""
    try:
        return await ProductService.delete_products(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to bulk delete products",
            detail=str(e),
            extra={
                "operation": "bulk_delete_products",
                "user_id": str(auth_user.user.id),
            },
        )


# --------------------------------------------------------------------------- #
#                              HSCode Endpoints                               #
# --------------------------------------------------------------------------- #
@hs_code_router.get("/hs-code/{hs_code}", response_model=GetHsCodeResponse)
async def get_hs_code(
    hs_code: UUID,
    auth_user: AuthenticatedUser,
) -> GetHsCodeResponse:
    """Retrieve a single HS code by ID for the authenticated user."""
    try:
        input_params = GetHsCodeRequest(id=hs_code)
        return await HSCodeService.get_hs_code_single(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve HS code",
            detail=str(e),
            extra={
                "operation": "get_hs_code",
                "user_id": str(auth_user.user.id),
                "hs_code": str(hs_code),
            },
        )


@hs_code_router.get("/hs-codes", response_model=GetHSCodesResponse)
async def get_hs_codes(
    auth_user: AuthenticatedUser,
    input_params: GetHSCodesRequest = Query(),
) -> GetHSCodesResponse:
    """List HS codes with filtering & pagination."""
    try:
        return await HSCodeService.get_hs_codes(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve HS codes",
            detail=str(e),
            extra={"operation": "get_hs_codes", "user_id": str(auth_user.user.id)},
        )


@hs_code_router.get("/hs-codes/all", response_model=GetHSCodesResponse)
async def get_all_hs_codes(
    auth_user: AuthenticatedUser,
) -> GetHSCodesResponse:
    """Retrieve all HS codes without pagination."""
    try:
        return await HSCodeService.get_all_hs_codes(auth_user)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve HS codes",
            detail=str(e),
            extra={"operation": "get_all_hs_codes", "user_id": str(auth_user.user.id)},
        )


@hs_code_router.post("/hs-codes", response_model=CreateHSCodeResponse)
async def create_hs_code(
    input_data: CreateHSCodeRequest, auth_user: AuthenticatedUser
) -> CreateHSCodeResponse:
    """Create a new HS code."""
    try:
        return await HSCodeService.create_hs_code(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create HS code",
            detail=str(e),
            extra={"operation": "create_hs_code", "user_id": str(auth_user.user.id)},
        )


@hs_code_router.patch("/hs-codes", response_model=UpdateHSCodeResponse)
async def update_hs_code(
    input_data: UpdateHSCodeRequest,
    auth_user: AuthenticatedUser,
) -> UpdateHSCodeResponse:
    """Update an existing HS code."""
    try:
        return await HSCodeService.update_hs_code(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update HS code",
            detail=str(e),
            extra={
                "operation": "update_hs_code",
                "user_id": str(auth_user.user.id),
            },
        )


@hs_code_router.delete("/hs-codes", response_model=DeleteHSCodeResponse)
async def delete_hs_codes(
    input_data: DeleteHSCodeRequest, auth_user: AuthenticatedUser
) -> DeleteHSCodeResponse:
    """Bulk delete HS codes by IDs."""
    try:
        return await HSCodeService.delete_hs_codes(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to bulk delete HS codes",
            detail=str(e),
            extra={
                "operation": "delete_hs_codes",
                "user_id": str(auth_user.user.id),
            },
        )
