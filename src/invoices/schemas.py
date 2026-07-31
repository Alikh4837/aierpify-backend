# src\invoices\schemas.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import NonNegativeFloat
from sqlmodel import AutoString, Column, DateTime, Field, SQLModel, func

from src.customers.enums import RegistrationTypeEnum
from src.customers.schemas import CreateCustomerRequest, CustomerResponse
from src.enums import ProvinceEnum, SaleTypeEnum
from src.invoices.enums import (
    AdditionalTaxTypeEnum,
    InvoiceFBRStatusEnum,
    InvoiceFieldsEnum,
    InvoiceItemFieldsEnum,
    InvoiceStatusEnum,
    InvoiceTypeEnum,
)
from src.products.schemas import CreateProductRequest, ProductResponse
from src.schemas import (
    DeleteRequestMixin,
    DeleteResponseMixin,
    IDMixin,
    OptionalIDMixin,
    OptionalUserIDMixin,
    OrderedRequestMixin,
    PaginatedRequestMixin,
    PaginatedResponseMixin,
    TimestampMixin,
)
from src.users.schemas import FBRProfileResponse, UserProfileResponse


# ---------------------------------------------------------------------------- #
#                                 Base Schemas                                 #
# ---------------------------------------------------------------------------- #
class InvoiceBase(SQLModel):
    """
    An invoice document with tax calculations and FBR integration.

    Attributes:
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (NonNegativeFloat): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
    """

    __tablename__ = "invoices"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the user who created this invoice.",
    )
    customer_id: UUID = Field(
        foreign_key="customers.id",
        ondelete="RESTRICT",
        nullable=False,
        description="ID of the customer this invoice is for.",
    )
    invoice_number: str = Field(
        nullable=False,
        description="Unique invoice number.",
    )
    issue_date: datetime = Field(
        description="Date and time when the invoice was issued.",
        sa_column=Column(
            "issue_date",
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Due date for payment.",
        sa_column=Column("due_date", DateTime(timezone=True), nullable=True),
    )
    subtotal: NonNegativeFloat = Field(
        nullable=False,
        description="Subtotal amount before taxes and discounts.",
    )
    discount_percentage: NonNegativeFloat = Field(
        default=0.0,
        nullable=False,
        description="Discount percentage applied.",
    )
    discount_amount: NonNegativeFloat = Field(
        default=0.0,
        nullable=False,
        description="Total discount amount applied.",
    )
    tax_amount: NonNegativeFloat = Field(
        nullable=False,
        description="Total tax amount.",
    )
    total_amount: NonNegativeFloat = Field(
        nullable=False,
        description="Final total amount after all calculations.",
    )
    status: InvoiceStatusEnum = Field(
        default=InvoiceStatusEnum.DRAFT,
        description="Current status of the invoice (e.g., 'draft', 'sent', 'paid').",
        sa_column=Column(
            "status",
            AutoString,
            nullable=False,
            server_default=InvoiceStatusEnum.DRAFT.value,
        ),
    )
    notes: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Additional notes or comments.",
    )
    invoice_type: Optional[InvoiceTypeEnum] = Field(
        default=None,
        description="Type of invoice (e.g., 'Sale Invoice', 'Debit Note').",
        sa_column=Column("invoice_type", AutoString, nullable=True),
    )
    additional_tax_type: Optional[AdditionalTaxTypeEnum] = Field(
        default=AdditionalTaxTypeEnum.NONE,
        description="Type of additional tax applied.",
        sa_column=Column(
            "additional_tax_type",
            AutoString,
            nullable=False,
            server_default=AdditionalTaxTypeEnum.NONE.value,
        ),
    )
    additional_tax_percentage: Optional[NonNegativeFloat] = Field(
        default=0.0,
        nullable=True,
        description="Percentage of additional tax applied.",
    )
    additional_tax_amount: Optional[NonNegativeFloat] = Field(
        default=0.0,
        nullable=True,
        description="Additional tax amount applied.",
    )
    extra_tax_amount: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Additional extra tax amount.",
    )
    further_tax_amount: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Further tax amount.",
    )
    federal_advance_duty_payable_amount: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Federal Advance Duty payable amount.",
    )
    fbr_validated: bool = Field(
        default=False,
        nullable=False,
        description="Whether the invoice has been validated with FBR.",
    )
    fbr_status: InvoiceFBRStatusEnum = Field(
        default=InvoiceFBRStatusEnum.PENDING,
        description="Status of FBR submission.",
        sa_column=Column(
            "fbr_status",
            AutoString,
            nullable=False,
            server_default=InvoiceFBRStatusEnum.PENDING.value,
        ),
    )
    fbr_reference: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Reference number from FBR system.",
    )


class InvoiceItemBase(SQLModel):
    """
    A line item within an invoice.

    Attributes:
        invoice_id (UUID): ID of the invoice this item belongs to.
        product_id (UUID): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (NonNegativeFloat): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (NonNegativeFloat): Discount percentage applied to this item.
        tax_rate (NonNegativeFloat): Tax rate applied to this item.
        line_total (NonNegativeFloat): Total amount for this line item.
    """

    __tablename__ = "invoice_items"  # type: ignore

    invoice_id: UUID = Field(
        foreign_key="invoices.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the invoice this item belongs to.",
    )
    product_id: UUID = Field(
        foreign_key="products.id",
        ondelete="RESTRICT",
        nullable=False,
        description="ID of the product being invoiced.",
    )
    sale_type: Optional[SaleTypeEnum] = Field(
        default=None,
        description="Type of sale for this item.",
        sa_column=Column("sale_type", AutoString, nullable=True),
    )
    quantity: NonNegativeFloat = Field(
        nullable=False,
        description="Quantity of the product.",
    )
    unit_price: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Unit price for this line item.",
    )
    retail_price: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Retail price for this line item.",
    )
    discount_percentage: NonNegativeFloat = Field(
        default=0.0,
        nullable=False,
        description="Discount percentage applied to this item.",
    )
    tax_rate: NonNegativeFloat = Field(
        default=18.0,
        nullable=False,
        description="Tax rate applied to this item.",
    )
    line_total: NonNegativeFloat = Field(
        nullable=False,
        description="Total amount for this line item.",
    )


# ---------------------------------------------------------------------------- #
#                             Endpoint I/O Schemas                             #
# ---------------------------------------------------------------------------- #
# --------------------------------- Invoice --------------------------------- #
class InvoiceResponse(TimestampMixin, InvoiceBase, IDMixin):
    """
    Response model for an invoice.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class InvoiceResponseList(SQLModel):
    """
    Response model for a list of invoices.

    Attributes:
        data (List[InvoiceResponse]): List of invoice records.
    """

    data: List[InvoiceResponse] = Field(
        default=[], description="List of invoice records."
    )


class CreateInvoiceRequest(InvoiceBase):
    """
    Request model for creating a new invoice.

    Attributes:
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who created this invoice."
    )


class CreateInvoiceResponse(InvoiceResponse):
    """
    Response model for creating a new invoice.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetInvoiceRequest(OptionalUserIDMixin, IDMixin):
    """
    Request model for retrieving an invoice by ID.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who created this invoice.
    """

    pass


class GetInvoicesRequest(
    OrderedRequestMixin[InvoiceFieldsEnum],
    PaginatedRequestMixin,
    InvoiceBase,
    OptionalIDMixin,
):
    """
    Request model for retrieving invoices with filtering and pagination.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who created this invoice.
        customer_id (Optional[UUID]): ID of the customer this invoice is for.
        invoice_number (Optional[str]): Unique invoice number.
        issue_date (Optional[datetime]): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (Optional[NonNegativeFloat]): Subtotal amount before taxes and discounts.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied.
        discount_amount (Optional[NonNegativeFloat]): Total discount amount applied.
        tax_amount (Optional[NonNegativeFloat]): Total tax amount.
        total_amount (Optional[NonNegativeFloat]): Final total amount after all calculations.
        status (Optional[str]): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (Optional[bool]): Whether the invoice has been validated with FBR.
        fbr_status (Optional[str]): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        page (int): Page number for pagination.
        page_size (int): Number of records per page for pagination.
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[InvoiceFieldsEnum]): Field to order by.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who created this invoice."
    )

    customer_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the customer this invoice is for."
    )

    invoice_number: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Unique invoice number."
    )

    issue_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None, description="Date and time when the invoice was issued."
    )

    subtotal: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Subtotal amount before taxes and discounts."
    )

    discount_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Discount percentage applied."
    )

    discount_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total discount amount applied."
    )

    tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total tax amount."
    )

    status: Optional[InvoiceStatusEnum] = Field(  # type: ignore[override]
        default=None,
        description="Current status of the invoice (e.g., 'draft', 'sent', 'paid').",
    )

    fbr_validated: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether the invoice has been validated with FBR."
    )

    fbr_status: Optional[InvoiceFBRStatusEnum] = Field(  # type: ignore[override]
        default=None, description="Status of FBR submission."
    )

    total_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Final total amount after all calculations."
    )

    order_by: Optional[InvoiceFieldsEnum] = Field(
        default=InvoiceFieldsEnum.CREATED_AT,
        description="Field to order the results by.",
    )


class GetInvoicesResponse(PaginatedResponseMixin, InvoiceResponseList):
    """
    Response model for retrieving invoices.

    Attributes:
        data (list[InvoiceResponse]): List of invoice records.
        total (int): Total number of records available.
        next_page (bool): Indicates if there is a next page.
    """

    pass


class GetInvoiceResponse(InvoiceResponse):
    """
    Response model for retrieving an invoice.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UpdateInvoiceRequest(InvoiceBase, IDMixin):
    """
    Request model for updating an existing invoice.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who created this invoice.
        customer_id (Optional[UUID]): ID of the customer this invoice is for.
        invoice_number (Optional[str]): Unique invoice number.
        issue_date (Optional[datetime]): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (Optional[NonNegativeFloat]): Subtotal amount before taxes and discounts.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied.
        discount_amount (Optional[NonNegativeFloat]): Total discount amount applied.
        tax_amount (Optional[NonNegativeFloat]): Total tax amount.
        total_amount (Optional[NonNegativeFloat]): Final total amount after all calculations.
        status (Optional[str]): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (Optional[bool]): Whether the invoice has been validated with FBR.
        fbr_status (Optional[str]): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who created this invoice."
    )
    customer_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the customer this invoice is for."
    )
    invoice_number: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Unique invoice number."
    )
    issue_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None, description="Date and time when the invoice was issued."
    )
    due_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None, description="Due date for payment."
    )
    subtotal: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Subtotal amount before taxes and discounts."
    )
    discount_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Discount percentage applied."
    )
    discount_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total discount amount applied."
    )
    tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total tax amount."
    )
    total_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Final total amount after all calculations."
    )
    status: Optional[str] = Field(  # type: ignore[override]
        default=None,
        description="Current status of the invoice (e.g., 'draft', 'sent', 'paid').",
    )
    notes: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Additional notes or comments."
    )
    invoice_type: Optional[str] = Field(  # type: ignore[override]
        default=None,
        description="Type of invoice (e.g., 'Sale Invoice', 'Debit Note').",
    )
    additional_tax_type: Optional[AdditionalTaxTypeEnum] = Field(  # type: ignore[override]
        default=None, description="Type of additional tax applied."
    )
    additional_tax_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore
        default=None, description="Percentage of additional tax applied."
    )
    additional_tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Additional tax amount applied."
    )
    extra_tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Additional extra tax amount."
    )
    further_tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Further tax amount."
    )
    federal_advance_duty_payable_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Federal Advance Duty payable amount."
    )
    fbr_validated: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether the invoice has been validated with FBR."
    )
    fbr_status: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Status of FBR submission."
    )
    fbr_reference: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Reference number from FBR system."
    )


class UpdateInvoiceResponse(InvoiceResponse):
    """
    Response model for updating an existing invoice.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_percentage (NonNegativeFloat): Discount percentage applied.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        additional_tax_type (Optional[AdditionalTaxTypeEnum]): Type of additional tax applied.
        additional_tax_percentage (Optional[NonNegativeFloat]): Percentage of additional tax applied.
        additional_tax_amount (Optional[NonNegativeFloat]): Additional tax amount applied.
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class DeleteInvoiceRequest(OptionalUserIDMixin, DeleteRequestMixin):
    """
    Request model for deleting an invoice.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    pass


class DeleteInvoiceResponse(DeleteResponseMixin):
    """
    Response model for deleting an invoice.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass


class ExportInvoicesExcelRequest(OptionalUserIDMixin):
    """
    Request model for exporting invoices to Excel.

    Attributes:
        id (List[UUID]): Unique identifiers for the invoices to export.
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    id: List[UUID] = Field(description="Unique identifiers for the invoices to export.")


# ------------------------------- Invoice Item -------------------------------- #
class InvoiceItemResponse(TimestampMixin, InvoiceItemBase, IDMixin):
    """
    Response model for an invoice line item.

    Attributes:
        id (UUID): Unique identifier for the record.
        invoice_id (UUID): ID of the invoice this item belongs to.
        product_id (UUID): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (NonNegativeFloat): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (NonNegativeFloat): Discount percentage applied to this item.
        tax_rate (NonNegativeFloat): Tax rate applied to this item.
        line_total (NonNegativeFloat): Total amount for this line item.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class InvoiceItemResponseList(SQLModel):
    """
    Response model for a list of invoice line items.

    Attributes:
        data (List[InvoiceItemResponse]): List of invoice item records.
    """

    data: List[InvoiceItemResponse] = Field(
        default=[], description="List of invoice item records."
    )


class CreateInvoiceItemRequest(InvoiceItemBase):
    """
    Request model for creating a new invoice line item.

    Attributes:
        invoice_id (UUID): ID of the invoice this item belongs to.
        product_id (UUID): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (NonNegativeFloat): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (NonNegativeFloat): Discount percentage applied to this item.
        tax_rate (NonNegativeFloat): Tax rate applied to this item.
        line_total (NonNegativeFloat): Total amount for this line item.
    """

    pass


class CreateInvoiceItemResponse(InvoiceItemResponse):
    """
    Response model for creating a new invoice line item.

    Attributes:
        invoice_id (UUID): ID of the invoice this item belongs to.
        product_id (UUID): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (NonNegativeFloat): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (NonNegativeFloat): Discount percentage applied to this item.
        tax_rate (NonNegativeFloat): Tax rate applied to this item.
        line_total (NonNegativeFloat): Total amount for this line item.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class CreateInvoiceItemsRequest(SQLModel):
    """
    Request model for creating multiple invoice line items in a single request.

    Attributes:
        data (List[InvoiceItemBase]): List of invoice item creation requests.
    """

    data: List[InvoiceItemBase] = Field(
        description="List of invoice item creation requests.",
    )


class CreateInvoiceItemsResponse(SQLModel):
    """
    Response model for creating multiple invoice line items.

    Attributes:
        data (List[InvoiceItemResponse]): List of created invoice item records.
    """

    data: List[InvoiceItemResponse] = Field(
        description="List of created invoice item records."
    )


class GetInvoiceItemsRequest(
    OrderedRequestMixin,
    PaginatedRequestMixin,
    InvoiceItemBase,
    OptionalIDMixin,
):
    """
    Request model for retrieving invoice line items with filtering and pagination.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        invoice_id (Optional[UUID]): ID of the invoice this item belongs to.
        product_id (Optional[UUID]): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (Optional[NonNegativeFloat]): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied to this item.
        tax_rate (Optional[NonNegativeFloat]): Tax rate applied to this item.
        line_total (Optional[NonNegativeFloat]): Total amount for this line item.
        page (int): Page number for pagination.
        page_size (int): Number of records per page for pagination.
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[InvoiceItemFieldsEnum]): Field to order by.
    """

    invoice_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the invoice this item belongs to."
    )

    product_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the product being invoiced."
    )

    quantity: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Quantity of the product."
    )

    discount_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Discount percentage applied to this item."
    )

    tax_rate: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Tax rate applied to this item."
    )

    line_total: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total amount for this line item."
    )

    order_by: Optional[InvoiceItemFieldsEnum] = Field(
        default=InvoiceItemFieldsEnum.CREATED_AT,
        description="Field to order the results by.",
    )


class GetInvoiceItemsResponse(PaginatedResponseMixin, InvoiceItemResponseList):
    """
    Response model for retrieving invoice line items.

    Attributes:
        data (list[InvoiceItemResponse]): List of invoice item records.
        total (int): Total number of records available.
        next_page (bool): Indicates if there is a next page.
    """

    pass


class UpdateInvoiceItemRequest(InvoiceItemBase, IDMixin):
    """
    Request model for updating an existing invoice line item.

    Attributes:
        id (UUID): Unique identifier for the record.
        invoice_id (Optional[UUID]): ID of the invoice this item belongs to.
        product_id (Optional[UUID]): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (Optional[NonNegativeFloat]): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied to this item.
        tax_rate (Optional[NonNegativeFloat]): Tax rate applied to this item.
        line_total (Optional[NonNegativeFloat]): Total amount for this line item.
    """

    invoice_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the invoice this item belongs to."
    )
    product_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the product being invoiced."
    )
    sale_type: Optional[SaleTypeEnum] = Field(  # type: ignore[override]
        default=None, description="Type of sale for this item."
    )
    quantity: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Quantity of the product."
    )
    unit_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Unit price for this line item."
    )
    retail_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, nullable=True, description="Retail price for this line item."
    )
    discount_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Discount percentage applied to this item."
    )
    tax_rate: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Tax rate applied to this item."
    )
    line_total: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total amount for this line item."
    )


class UpdateInvoiceItemResponse(InvoiceItemResponse):
    """
    Response model for updating an existing invoice line item.

    Attributes:
        invoice_id (UUID): ID of the invoice this item belongs to.
        product_id (UUID): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (NonNegativeFloat): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        retail_price (Optional[NonNegativeFloat]): Retail price for this line item.
        discount_percentage (NonNegativeFloat): Discount percentage applied to this item.
        tax_rate (NonNegativeFloat): Tax rate applied to this item.
        line_total (NonNegativeFloat): Total amount for this line item.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UpdateInvoiceItemsRequest(SQLModel):
    """
    Request model for updating multiple invoice line items in a single request.

    Attributes:
        data (List[UpdateInvoiceItemRequest]): List of invoice item update requests.
    """

    data: List[UpdateInvoiceItemRequest] = Field(
        description="List of invoice item update requests.",
    )


class UpdateInvoiceItemsResponse(SQLModel):
    """
    Response model for updating multiple invoice line items.

    Attributes:
        data (List[InvoiceItemResponse]): List of updated invoice item records.
    """

    data: List[InvoiceItemResponse] = Field(
        description="List of updated invoice item records."
    )


class DeleteInvoiceItemRequest(OptionalUserIDMixin, DeleteRequestMixin):
    """
    Request model for deleting an invoice line item.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    pass


class DeleteInvoiceItemResponse(DeleteResponseMixin):
    """
    Response model for deleting an invoice line item.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass


# ----------------------------- Invoice Complete ----------------------------- #
class InvoiceCompleteResponse(InvoiceResponse):
    """
    Complete response model for an invoice including its line items.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
        user_profile (UserProfileResponse): User profile details of the invoice creator.
        fbr_profile (FBRProfilePublicResponse): FBR profile details associated with the invoice.
        customer (CustomerResponse): Customer details associated with this invoice.
        items (List[InvoiceItemResponse]): List of associated invoice line items.
        products (List[ProductResponse]): List of associated products.
    """

    user_profile: UserProfileResponse = Field(
        description="User profile details of the invoice creator."
    )
    fbr_profile: FBRProfileResponse = Field(
        description="FBR profile details associated with the invoice."
    )
    customer: CustomerResponse = Field(
        description="Customer details associated with this invoice."
    )
    items: List[InvoiceItemResponse] = Field(
        description="List of associated invoice line items.",
    )
    products: List[ProductResponse] = Field(
        description="List of associated products.",
    )


class GetInvoiceCompleteResponse(InvoiceCompleteResponse):
    """
    Complete response model for retrieving an invoice including its line items.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who created this invoice.
        customer_id (UUID): ID of the customer this invoice is for.
        invoice_number (str): Unique invoice number.
        issue_date (datetime): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (NonNegativeFloat): Subtotal amount before taxes and discounts.
        discount_amount (NonNegativeFloat): Total discount amount applied.
        tax_amount (NonNegativeFloat): Total tax amount.
        total_amount (NonNegativeFloat): Final total amount after all calculations.
        status (InvoiceStatusEnum): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (bool): Whether the invoice has been validated with FBR.
        fbr_status (str): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
        user_profile (UserProfileResponse): User profile details of the invoice creator.
        fbr_profile (FBRProfilePublicResponse): FBR profile details associated with the invoice.
        customer (CustomerResponse): Customer details associated with this invoice.
        items (List[InvoiceItemResponse]): List of associated invoice line items.
        products (List[ProductResponse]): List of associated products.
    """

    pass


# ------------------------------ Invoice Import ------------------------------ #
class InvoiceImportValidationError(SQLModel):
    """
    Response model for validation errors encountered while parsing invoice import files.

    Attributes:
        row (int): Excel row number where the validation error occurred.
        field (str): Spreadsheet column name associated with the validation error.
        message (str): Human-readable description of the validation error.
        value (Optional[str]): Raw cell value that triggered the validation error.
    """

    row: int = Field(
        description="Excel row number where the validation error occurred."
    )
    field: str = Field(
        description="Spreadsheet column name associated with the validation error."
    )
    message: str = Field(
        description="Human-readable description of the validation error."
    )
    value: Optional[str] = Field(
        default=None,
        description="Raw cell value that triggered the validation error.",
    )


class InvoiceImportParsedInvoiceItem(InvoiceItemBase):
    """
    Parsed invoice line item derived from an import file.

    Attributes:
        invoice_id (Optional[UUID]): ID of the invoice this item belongs to.
        product_id (Optional[UUID]): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (Optional[NonNegativeFloat]): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied to this item.
        tax_rate (Optional[NonNegativeFloat]): Tax rate applied to this item.
        line_total (Optional[NonNegativeFloat]): Total amount for this line item.
        product_description (Optional[str]): Product description provided in the spreadsheet.
        hs_code (Optional[str]): HS code associated with the product.
        unit_of_measurement (Optional[str]): Unit of measurement for the product quantity.
        value_of_sales_excl_st (Optional[NonNegativeFloat]): Value of sales excluding sales tax.
        sales_tax_fed_in_st_mode (Optional[NonNegativeFloat]): Sales tax or FED amount in ST mode.
        fixed_notified_value_or_st_withheld_as_wh_agent (Optional[NonNegativeFloat]): Fixed or notified value withheld as withholding agent.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Extra tax amount applied to the product.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applied to the product.
        sro_number (Optional[str]): SRO number referenced for the product.
        sro_item_serial_number (Optional[str]): SRO item serial number referenced for the product.
    """

    invoice_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the invoice this item belongs to."
    )
    product_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the product being invoiced."
    )
    sale_type: Optional[SaleTypeEnum] = Field(  # type: ignore[override]
        default=None, description="Type of sale for this item."
    )
    quantity: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Quantity of the product."
    )
    unit_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Unit price for this line item."
    )
    discount_percentage: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Discount percentage applied to this item."
    )
    tax_rate: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Tax rate applied to this item."
    )
    line_total: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total amount for this line item."
    )
    product_description: Optional[str] = Field(
        default=None,
        description="Product description provided in the spreadsheet.",
    )
    hs_code: Optional[str] = Field(
        default=None,
        description="HS code associated with the product.",
    )
    unit_of_measurement: Optional[str] = Field(
        default=None,
        description="Unit of measurement for the product quantity.",
    )
    value_of_sales_excl_st: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Value of sales excluding sales tax.",
    )
    sales_tax_fed_in_st_mode: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Sales tax or FED amount in ST mode.",
    )
    fixed_notified_value_or_st_withheld_as_wh_agent: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Fixed or notified value withheld as withholding agent.",
    )
    sales_tax_withheld: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Sales tax withheld amount.",
    )
    extra_tax: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Extra tax amount applied to the product.",
    )
    further_tax: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Further tax amount applied to the product.",
    )
    sro_number: Optional[str] = Field(
        default=None,
        description="SRO number referenced for the product.",
    )
    sro_item_serial_number: Optional[str] = Field(
        default=None,
        description="SRO item serial number referenced for the product.",
    )


class InvoiceImportParsedInvoice(InvoiceBase):
    """
    Parsed invoice derived from an import file, including associated line items and buyer details.

    Attributes:
        user_id (Optional[UUID]): ID of the user who created this invoice.
        customer_id (Optional[UUID]): ID of the customer this invoice is for.
        invoice_number (Optional[str]): Unique invoice number.
        issue_date (Optional[datetime]): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (Optional[NonNegativeFloat]): Subtotal amount before taxes and discounts.
        discount_amount (Optional[NonNegativeFloat]): Total discount amount applied.
        tax_amount (Optional[NonNegativeFloat]): Total tax amount.
        total_amount (Optional[NonNegativeFloat]): Final total amount after all calculations.
        status (Optional[str]): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (Optional[bool]): Whether the invoice has been validated with FBR.
        fbr_status (Optional[str]): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        registration_number (Optional[str]): Registration number supplied in the import file.
        buyer_name (Optional[str]): Name associated with the buyer in the import file.
        phone_number (Optional[str]): Phone number supplied for the buyer in the import file.
        email (Optional[str]): Email address supplied for the buyer in the import file.
        buyer_registration_type (Optional[RegistrationTypeEnum]): Registration type supplied for the buyer in the import file.
        province (Optional[ProvinceEnum]): Province supplied for the buyer in the import file.
        address (Optional[str]): Address supplied for the buyer in the import file.
        items (List[InvoiceImportParsedInvoiceItem]): Parsed invoice items associated with this invoice.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who created this invoice."
    )
    customer_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the customer this invoice is for."
    )
    invoice_number: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Unique invoice number."
    )
    issue_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None, description="Date and time when the invoice was issued."
    )
    due_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None, description="Due date for payment."
    )
    subtotal: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Subtotal amount before taxes and discounts."
    )
    discount_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total discount amount applied."
    )
    tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Total tax amount."
    )
    total_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Final total amount after all calculations."
    )
    status: Optional[InvoiceStatusEnum] = Field(  # type: ignore[override]
        default=None,
        description="Current status of the invoice (e.g., 'draft', 'sent', 'paid').",
    )
    notes: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Additional notes or comments."
    )
    invoice_type: Optional[str] = Field(  # type: ignore[override]
        default=None,
        description="Type of invoice (e.g., 'Sale Invoice', 'Debit Note').",
    )
    extra_tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Additional extra tax amount."
    )
    further_tax_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Further tax amount."
    )
    federal_advance_duty_payable_amount: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Federal Advance Duty payable amount."
    )
    fbr_validated: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether the invoice has been validated with FBR."
    )
    fbr_status: Optional[InvoiceFBRStatusEnum] = Field(  # type: ignore[override]
        default=None, description="Status of FBR submission."
    )
    fbr_reference: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Reference number from FBR system."
    )
    registration_number: Optional[str] = Field(
        default=None,
        description="Registration number supplied in the import file.",
    )
    buyer_name: Optional[str] = Field(
        default=None, description="Name associated with the buyer in the import file."
    )
    phone_number: Optional[str] = Field(
        default=None,
        description="Phone number supplied for the buyer in the import file.",
    )
    email: Optional[str] = Field(
        default=None,
        description="Email address supplied for the buyer in the import file.",
    )
    buyer_registration_type: Optional[RegistrationTypeEnum] = Field(
        default=None,
        description="Registration type supplied for the buyer in the import file.",
    )
    province: Optional[ProvinceEnum] = Field(
        default=None, description="Province supplied for the buyer in the import file."
    )
    address: Optional[str] = Field(
        default=None, description="Address supplied for the buyer in the import file."
    )
    items: List[InvoiceImportParsedInvoiceItem] = Field(
        default_factory=list,
        description="Parsed invoice items associated with this invoice.",
    )


class InvoiceImportParseResponse(SQLModel):
    """
    Response model for parsing invoice import files.

    Attributes:
        success (bool): Indicates if the import completed without validation errors.
        data (List[InvoiceImportParsedInvoice]): Parsed invoices grouped by invoice number.
        errors (List[InvoiceImportValidationError]): Validation errors encountered during parsing.
        total_rows (int): Total number of rows processed from the spreadsheet.
        valid_invoices (int): Number of invoices successfully parsed from the spreadsheet.
        processed_items (int): Total number of invoice items included in the parsed invoices.
    """

    success: bool = Field(
        description="Indicates if the import completed without validation errors."
    )
    data: List[InvoiceImportParsedInvoice] = Field(
        default_factory=list,
        description="Parsed invoices grouped by invoice number.",
    )
    errors: List[InvoiceImportValidationError] = Field(
        default_factory=list,
        description="Validation errors encountered during parsing.",
    )
    total_rows: int = Field(
        description="Total number of rows processed from the spreadsheet.",
    )
    valid_invoices: int = Field(
        description="Number of invoices successfully parsed from the spreadsheet.",
    )
    processed_items: int = Field(
        description="Total number of invoice items included in the parsed invoices.",
    )


class InvoiceImportSubmitInvoiceItem(InvoiceImportParsedInvoiceItem):
    """
    Request model for submitting an imported invoice line item.

    Attributes:
        invoice_id (Optional[UUID]): ID of the invoice this item belongs to.
        product_id (Optional[UUID]): ID of the product being invoiced.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        quantity (Optional[NonNegativeFloat]): Quantity of the product.
        unit_price (Optional[NonNegativeFloat]): Unit price for this line item.
        discount_percentage (Optional[NonNegativeFloat]): Discount percentage applied to this item.
        tax_rate (Optional[NonNegativeFloat]): Tax rate applied to this item.
        line_total (Optional[NonNegativeFloat]): Total amount for this line item.
        product_description (Optional[str]): Product description provided in the spreadsheet.
        hs_code (Optional[str]): HS code associated with the product.
        unit_of_measurement (Optional[str]): Unit of measurement for the product quantity.
        value_of_sales_excl_st (Optional[NonNegativeFloat]): Value of sales excluding sales tax.
        sales_tax_fed_in_st_mode (Optional[NonNegativeFloat]): Sales tax or FED amount in ST mode.
        fixed_notified_value_or_st_withheld_as_wh_agent (Optional[NonNegativeFloat]): Fixed or notified value withheld as withholding agent.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Extra tax amount applied to the product.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applied to the product.
        sro_number (Optional[str]): SRO number referenced for the product.
        sro_item_serial_number (Optional[str]): SRO item serial number referenced for the product.
        product (Optional[CreateProductRequest]): Product details used to create a product when product_id is not provided.
    """

    product: Optional[CreateProductRequest] = Field(
        default=None,
        description="Product details used to create a product when product_id is not provided.",
    )


class InvoiceImportSubmitInvoice(InvoiceImportParsedInvoice):
    """
    Request model for submitting an imported invoice with nested items.

    Attributes:
        user_id (Optional[UUID]): ID of the user who created this invoice.
        customer_id (Optional[UUID]): ID of the customer this invoice is for.
        invoice_number (Optional[str]): Unique invoice number.
        issue_date (Optional[datetime]): Date and time when the invoice was issued.
        due_date (Optional[datetime]): Due date for payment.
        subtotal (Optional[NonNegativeFloat]): Subtotal amount before taxes and discounts.
        discount_amount (Optional[NonNegativeFloat]): Total discount amount applied.
        tax_amount (Optional[NonNegativeFloat]): Total tax amount.
        total_amount (Optional[NonNegativeFloat]): Final total amount after all calculations.
        status (Optional[str]): Current status of the invoice (e.g., 'draft', 'sent', 'paid').
        notes (Optional[str]): Additional notes or comments.
        invoice_type (Optional[InvoiceTypeEnum]): Type of invoice (e.g., 'Sale Invoice', 'Debit Note').
        extra_tax_amount (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax_amount (Optional[NonNegativeFloat]): Further tax amount.
        federal_advance_duty_payable_amount (Optional[NonNegativeFloat]): FAD payable amount.
        fbr_validated (Optional[bool]): Whether the invoice has been validated with FBR.
        fbr_status (Optional[str]): Status of FBR submission.
        fbr_reference (Optional[str]): Reference number from FBR system.
        registration_number (Optional[str]): Registration number supplied in the import file.
        buyer_name (Optional[str]): Name associated with the buyer in the import file.
        phone_number (Optional[str]): Phone number supplied for the buyer in the import file.
        email (Optional[str]): Email address supplied for the buyer in the import file.
        buyer_registration_type (Optional[RegistrationTypeEnum]): Registration type supplied for the buyer in the import file.
        province (Optional[ProvinceEnum]): Province supplied for the buyer in the import file.
        address (Optional[str]): Address supplied for the buyer in the import file.
        items (List[InvoiceImportSubmitInvoiceItem]): Parsed invoice items associated with this invoice submission.
        customer (Optional[CreateCustomerRequest]): Customer details used to create a customer when customer_id is not provided.
    """

    items: List[InvoiceImportSubmitInvoiceItem] = Field(  # type: ignore[override]
        default_factory=list,
        description="Parsed invoice items associated with this invoice submission.",
    )
    customer: Optional[CreateCustomerRequest] = Field(
        default=None,
        description="Customer details used to create a customer when customer_id is not provided.",
    )


class InvoiceImportSubmitInvoiceResult(SQLModel):
    """
    Response model for a submitted imported invoice.

    Attributes:
        invoice (CreateInvoiceResponse): Created invoice details.
        items (List[InvoiceItemResponse]): Created invoice item details associated with the invoice.
    """

    invoice: CreateInvoiceResponse = Field(
        description="Created invoice details.",
    )
    items: List[InvoiceItemResponse] = Field(
        default_factory=list,
        description="Created invoice item details associated with the invoice.",
    )


class InvoiceImportSubmitResponse(SQLModel):
    """
    Response model for submitting imported invoices for creation.

    Attributes:
        success (bool): Indicates if all invoices were created successfully.
        invoices (List[InvoiceImportSubmitInvoiceResult]): List of created invoices with their associated items.
    """

    success: bool = Field(
        description="Indicates if all invoices were created successfully."
    )
    invoices: List[InvoiceImportSubmitInvoiceResult] = Field(
        default_factory=list,
        description="List of created invoices with their associated items.",
    )


class InvoiceImportSubmitRequest(SQLModel):
    """
    Request model for submitting parsed invoices for creation.

    Attributes:
        invoices (List[InvoiceImportSubmitInvoice]): List of parsed invoices to create.
    """

    invoices: List[InvoiceImportSubmitInvoice] = Field(
        default_factory=list,
        description="List of parsed invoices to create.",
    )
