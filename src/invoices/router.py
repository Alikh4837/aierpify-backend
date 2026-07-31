# src\invoices\router.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from src.dependencies import AuthenticatedUser
from src.exceptions import ERROR_RESPONSES, InternalServerErrorException
from src.invoices.schemas import (
    CreateInvoiceItemsRequest,
    CreateInvoiceItemsResponse,
    CreateInvoiceRequest,
    CreateInvoiceResponse,
    DeleteInvoiceItemRequest,
    DeleteInvoiceItemResponse,
    DeleteInvoiceRequest,
    DeleteInvoiceResponse,
    ExportInvoicesExcelRequest,
    GetInvoiceCompleteResponse,
    GetInvoiceItemsRequest,
    GetInvoiceItemsResponse,
    GetInvoiceRequest,
    GetInvoiceResponse,
    GetInvoicesRequest,
    GetInvoicesResponse,
    InvoiceImportParseResponse,
    InvoiceImportSubmitRequest,
    InvoiceImportSubmitResponse,
    UpdateInvoiceItemRequest,
    UpdateInvoiceItemResponse,
    UpdateInvoiceItemsRequest,
    UpdateInvoiceItemsResponse,
    UpdateInvoiceRequest,
    UpdateInvoiceResponse,
)
from src.invoices.service import (
    InvoiceImportService,
    InvoiceItemService,
    InvoiceService,
)

router = APIRouter(prefix="/invoices", tags=["Invoices"], responses=ERROR_RESPONSES)


# --------------------------------------------------------------------------- #
#                              Invoice Endpoints                              #
# --------------------------------------------------------------------------- #
@router.get("/{invoice_id}", response_model=GetInvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    auth_user: AuthenticatedUser,
    user_id: Optional[UUID] = Query(default=None),
) -> GetInvoiceResponse:
    """Retrieve a single invoice by ID for the authenticated user."""
    try:
        input_params = GetInvoiceRequest(id=invoice_id, user_id=user_id)
        return await InvoiceService.get_invoice_single(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve invoice",
            detail=str(e),
            extra={
                "operation": "get_invoice",
                "user_id": str(auth_user.user.id),
                "invoice_id": str(invoice_id),
            },
        )


@router.get(
    "/{invoice_id}/complete",
    response_model=GetInvoiceCompleteResponse,
    tags=["Products", "Customers", "Users"],
)
async def get_invoice_complete(
    invoice_id: UUID,
    auth_user: AuthenticatedUser,
) -> GetInvoiceCompleteResponse:
    """Retrieve a single invoice with items by ID for the authenticated user."""
    try:
        input_params = GetInvoiceRequest(id=invoice_id)

        return await InvoiceService.get_invoice_single_complete(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve complete invoice",
            detail=str(e),
            extra={
                "operation": "get_invoice_complete",
                "user_id": str(auth_user.user.id),
                "invoice_id": str(invoice_id),
            },
        )


@router.get("", response_model=GetInvoicesResponse)
async def get_invoices(
    auth_user: AuthenticatedUser,
    input_params: GetInvoicesRequest = Query(),
) -> GetInvoicesResponse:
    """List invoices with filtering & pagination for the authenticated user."""
    try:
        return await InvoiceService.get_invoices(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve invoices",
            detail=str(e),
            extra={"operation": "list_invoices", "user_id": str(auth_user.user.id)},
        )


@router.post("", response_model=CreateInvoiceResponse)
async def create_invoice(
    input_data: CreateInvoiceRequest, auth_user: AuthenticatedUser
) -> CreateInvoiceResponse:
    """Create a new invoice."""
    try:
        return await InvoiceService.create_invoice(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create invoice",
            detail=str(e),
            extra={"operation": "create_invoice", "user_id": str(auth_user.user.id)},
        )


@router.patch("", response_model=UpdateInvoiceResponse)
async def update_invoice(
    input_data: UpdateInvoiceRequest,
    auth_user: AuthenticatedUser,
) -> UpdateInvoiceResponse:
    """Update an existing invoice."""
    try:
        return await InvoiceService.update_invoice(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update invoice",
            detail=str(e),
            extra={
                "operation": "update_invoice",
                "user_id": str(auth_user.user.id),
            },
        )


@router.delete("", response_model=DeleteInvoiceResponse)
async def delete_invoices(
    input_data: DeleteInvoiceRequest, auth_user: AuthenticatedUser
) -> DeleteInvoiceResponse:
    """Bulk delete invoices by IDs."""
    try:
        return await InvoiceService.delete_invoices(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to bulk delete invoices",
            detail=str(e),
            extra={
                "operation": "bulk_delete_invoices",
                "user_id": str(auth_user.user.id),
            },
        )


@router.post("/import/parse", response_model=InvoiceImportParseResponse)
async def parse_invoice_import(
    auth_user: AuthenticatedUser,
    file: UploadFile = File(...),
) -> InvoiceImportParseResponse:
    """Parse an uploaded Excel file into invoice and invoice item structures."""
    try:
        file_bytes = await file.read()
        return await InvoiceImportService.parse_import_file(
            auth_user=auth_user,
            filename=file.filename or "",
            file_bytes=file_bytes,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to parse invoice import file",
            detail=str(e),
            extra={
                "operation": "parse_invoice_import",
                "user_id": str(auth_user.user.id),
                "filename": file.filename,
            },
        )


@router.post("/import/submit", response_model=InvoiceImportSubmitResponse)
async def submit_invoice_import(
    input_data: InvoiceImportSubmitRequest,
    auth_user: AuthenticatedUser,
) -> InvoiceImportSubmitResponse:
    """Persist parsed invoices by creating customers, products, and invoice records."""

    try:
        return await InvoiceImportService.submit_imported_invoices(
            auth_user, input_data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to submit invoice import payload",
            detail=str(e),
            extra={
                "operation": "submit_invoice_import",
                "user_id": str(auth_user.user.id),
            },
        )


@router.post("/export/excel")
async def export_invoices_excel(
    input_data: ExportInvoicesExcelRequest,
    auth_user: AuthenticatedUser,
) -> StreamingResponse:
    """Export selected invoices in Excel format using the invoice import layout."""
    try:
        workbook_bytes, filename = await InvoiceImportService.export_invoices_excel(
            auth_user, input_data
        )
        return StreamingResponse(
            workbook_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to export invoices to Excel",
            detail=str(e),
            extra={
                "operation": "export_invoices_excel",
                "user_id": str(auth_user.user.id),
                "invoice_ids": [str(invoice_id) for invoice_id in input_data.id],
            },
        )


# --------------------------------------------------------------------------- #
#                            Invoice Item Endpoints                          #
# --------------------------------------------------------------------------- #
@router.get("/{invoice_id}/items", response_model=GetInvoiceItemsResponse)
async def get_invoice_items(
    invoice_id: UUID,
    auth_user: AuthenticatedUser,
    input_params: GetInvoiceItemsRequest = Query(),
) -> GetInvoiceItemsResponse:
    """List invoice items with filtering & pagination."""
    try:
        input_params.invoice_id = invoice_id
        return await InvoiceItemService.get_invoice_items(auth_user, input_params)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to retrieve invoice items",
            detail=str(e),
            extra={
                "operation": "list_invoice_items",
                "user_id": str(auth_user.user.id),
            },
        )


@router.post("/{invoice_id}/items", response_model=CreateInvoiceItemsResponse)
async def create_invoice_items(
    invoice_id: UUID,
    auth_user: AuthenticatedUser,
    input_data: CreateInvoiceItemsRequest,
) -> CreateInvoiceItemsResponse:
    """Create new invoice items."""
    try:
        return await InvoiceItemService.create_invoice_items(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to create invoice item",
            detail=str(e),
            extra={
                "operation": "create_invoice_item",
                "user_id": str(auth_user.user.id),
            },
        )


@router.patch("/{invoice_id}/items", response_model=UpdateInvoiceItemResponse)
async def update_invoice_item(
    invoice_id: UUID,
    input_data: UpdateInvoiceItemRequest,
    auth_user: AuthenticatedUser,
) -> UpdateInvoiceItemResponse:
    """Update an existing invoice item."""
    try:
        return await InvoiceItemService.update_invoice_item(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update invoice item",
            detail=str(e),
            extra={
                "operation": "update_invoice_item",
                "user_id": str(auth_user.user.id),
            },
        )


@router.patch("/{invoice_id}/items/batch", response_model=UpdateInvoiceItemsResponse)
async def update_invoice_items(
    invoice_id: UUID,
    input_data: UpdateInvoiceItemsRequest,
    auth_user: AuthenticatedUser,
) -> UpdateInvoiceItemsResponse:
    """Update an existing invoice item."""
    try:
        return await InvoiceItemService.update_invoice_items(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to update invoice items",
            detail=str(e),
            extra={
                "operation": "update_invoice_items",
                "user_id": str(auth_user.user.id),
            },
        )


@router.delete("/{invoice_id}/items", response_model=DeleteInvoiceItemResponse)
async def delete_invoice_items(
    invoice_id: UUID, input_data: DeleteInvoiceItemRequest, auth_user: AuthenticatedUser
) -> DeleteInvoiceItemResponse:
    """Bulk delete invoice items by IDs."""
    try:
        return await InvoiceItemService.delete_invoice_items(auth_user, input_data)

    except HTTPException:
        raise

    except Exception as e:
        raise InternalServerErrorException(
            message="Failed to bulk delete invoice items",
            detail=str(e),
            extra={
                "operation": "bulk_delete_invoice_items",
                "user_id": str(auth_user.user.id),
            },
        )
