# src\products\schemas.py
from typing import List, Optional, Union
from uuid import UUID

from pydantic import NonNegativeFloat
from sqlmodel import ARRAY, TEXT, AutoString, Column, Field, SQLModel

from src.enums import SaleTypeEnum
from src.products.enums import (
    HSCodeFieldsEnum,
    NumericTaxRateEnum,
    ProductFieldsEnum,
    SpecialTaxRateEnum,
    SroScheduleCodeEnum,
)
from src.schemas import (
    DeleteRequestMixin,
    DeleteResponseMixin,
    IDMixin,
    OptionalIDListMixin,
    OptionalIDMixin,
    OptionalUserIDMixin,
    OrderedRequestMixin,
    PaginatedRequestMixin,
    PaginatedResponseMixin,
    TimestampMixin,
)


# ---------------------------------------------------------------------------- #
#                                 Base Schemas                                 #
# ---------------------------------------------------------------------------- #
class ProductBase(SQLModel):
    """
    A product or service that can be invoiced.

    Attributes:
        user_id (UUID): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (SaleTypeEnum): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
    """

    __tablename__ = "products"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the user who owns this product.",
    )
    name: str = Field(
        nullable=False,
        description="Name of the product or service.",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Detailed description of the product.",
    )
    hs_code: str = Field(
        default=None,
        nullable=True,
        description="Harmonized System code for the product.",
    )
    sale_type: SaleTypeEnum = Field(
        default=None,
        description="Type of sale for this item.",
        sa_column=Column("sale_type", AutoString, nullable=True),
    )
    unit_price: NonNegativeFloat = Field(
        nullable=False,
        description="Base unit price of the product.",
    )
    unit_of_measurement: str = Field(
        default="pcs",
        nullable=False,
        description="Unit of measurement (e.g., 'pcs', 'kg', 'hours').",
    )
    tax_rate: Union[NumericTaxRateEnum, SpecialTaxRateEnum] = Field(
        default=NumericTaxRateEnum._18,
        description="Default tax rate percentage for this product.",
        sa_column=Column("tax_rate", AutoString, nullable=False),
    )
    retail_price: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Retail selling price.",
    )
    sales_tax_applicable: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Sales tax applicable amount.",
    )
    sales_tax_withheld: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Sales tax withheld amount.",
    )
    extra_tax: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Additional extra tax amount.",
    )
    further_tax: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Further tax amount applicable.",
    )
    federal_advance_duty_payable: Optional[NonNegativeFloat] = Field(
        default=None,
        nullable=True,
        description="Federal Advance Duty payable amount.",
    )
    sro_schedule_code: Optional[SroScheduleCodeEnum] = Field(
        default=SroScheduleCodeEnum._EMPTY,
        description="SRO schedule code for tax calculations.",
        sa_column=Column("sro_schedule_code", AutoString, nullable=True),
    )
    sro_serial_number: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Serial number from Sales Tax Special Regulatory Order.",
    )


class HSCodeBase(SQLModel):
    """
    Harmonized System (HS) codes for product classification.

    Attributes:
        hs_code (str): The HS code identifier.
        units_of_measurement (List[str]): Units of measurement for the HS code.
        description (str): Description of what the HS code represents.
    """

    __tablename__ = "hs_codes"  # type: ignore

    hs_code: str = Field(
        default=None,
        nullable=False,
        unique=True,
        description="The HS code identifier.",
    )
    units_of_measurement: List[str] = Field(
        default=None,
        description="Units of measurement for the HS code.",
        sa_column=Column("units_of_measurement", ARRAY(TEXT), nullable=False),
    )
    description: str = Field(
        default=None,
        nullable=False,
        description="Description of what the HS code represents.",
    )


# ---------------------------------------------------------------------------- #
#                             Endpoint I/O Schemas                             #
# ---------------------------------------------------------------------------- #
# --------------------------------- Product --------------------------------- #
class ProductResponse(TimestampMixin, ProductBase, IDMixin):
    """
    Response model for a product.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (SaleTypeEnum): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class ProductResponseList(SQLModel):
    """
    Response model for a list of products.

    Attributes:
        data (List[ProductResponse]): List of product records.
    """

    data: List[ProductResponse] = Field(
        default=[], description="List of product records."
    )


class CreateProductRequest(ProductBase):
    """
    Request model for creating a new product.

    Attributes:
        user_id (Optional[UUID]): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who owns this product."
    )

    sale_type: Optional[SaleTypeEnum] = Field(  # type: ignore[override]
        default=None,
        description="Type of sale for this item.",
    )


class CreateProductResponse(ProductResponse):
    """
    Response model for creating a new product.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (SaleTypeEnum): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetProductRequest(OptionalUserIDMixin, IDMixin):
    """
    Request model for retrieving a product by ID.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who owns this product.
    """

    pass


class GetProductsRequest(
    OrderedRequestMixin,
    PaginatedRequestMixin,
    ProductBase,
    OptionalIDListMixin,
):
    """
    Request model for retrieving products with filtering and pagination.

    Attributes:
        id (Optional[Union[List[UUID], UUID]]): Single or List of unique identifiers for the records.
        user_id (Optional[UUID]): ID of the user who owns this product.
        name (Optional[str]): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (Optional[str]): Harmonized System code for the product.
        sale_type (Optional[SaleTypeEnum]): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (Optional[str]): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (Optional[str]): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
        page (int): Page number for pagination.
        page_size (int): Number of records per page for pagination.
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[ProductFieldsEnum]): Field to order by.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who owns this product."
    )

    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the product or service."
    )

    hs_code: Optional[str] = Field(  # type: ignore[override]
        default=None,
        description="Harmonized System code for the product.",
    )

    sale_type: Optional[SaleTypeEnum] = Field(  # type: ignore[override]
        default=None,
        description="Type of sale for this item.",
    )

    unit_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Base unit price of the product."
    )

    unit_of_measurement: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Unit of measurement (e.g., 'pcs', 'kg', 'hours')."
    )

    tax_rate: Optional[Union[NumericTaxRateEnum, SpecialTaxRateEnum]] = Field(  # type: ignore[override]
        default=None, description="Default tax rate percentage for this product."
    )

    order_by: Optional[ProductFieldsEnum] = Field(  # type: ignore[override]
        default=None, description="Field to order by."
    )


class GetProductsResponse(PaginatedResponseMixin, ProductResponseList):
    """
    Response model for retrieving products.

    Attributes:
        data (list[ProductResponse]): List of product records.
        total (int): Total number of records available.
        next_page (bool): Indicates if there is a next page.
    """

    pass


class GetProductResponse(ProductResponse):
    """
    Response model for retrieving a product.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (SaleTypeEnum): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UpdateProductRequest(ProductBase, IDMixin):
    """
    Request model for updating an existing product.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who owns this product.
        name (Optional[str]): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        unit_price (Optional[NonNegativeFloat]): Base unit price of the product.
        unit_of_measurement (Optional[str]): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (Optional[str]): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who owns this product."
    )
    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the product or service."
    )
    description: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Detailed description of the product."
    )
    hs_code: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Harmonized System code for the product."
    )
    sale_type: Optional[SaleTypeEnum] = Field(  # type: ignore[override]
        default=None,
        description="Type of sale for this item.",
    )
    unit_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Base unit price of the product."
    )
    unit_of_measurement: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Unit of measurement (e.g., 'pcs', 'kg', 'hours')."
    )
    tax_rate: Optional[Union[NumericTaxRateEnum, SpecialTaxRateEnum]] = Field(  # type: ignore[override]
        default=None, description="Default tax rate percentage for this product."
    )
    retail_price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Retail selling price."
    )
    sales_tax_applicable: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Sales tax applicable amount."
    )
    sales_tax_withheld: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Sales tax withheld amount."
    )
    extra_tax: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Additional extra tax amount."
    )
    further_tax: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Further tax amount applicable."
    )
    federal_advance_duty_payable: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Federal Advance Duty payable amount."
    )
    sro_schedule_code: Optional[SroScheduleCodeEnum] = Field(  # type: ignore[override]
        default=None, description="SRO schedule code for tax calculations."
    )
    sro_serial_number: Optional[str] = Field(  # type: ignore[override]
        default=None,
        description="Serial number from Sales Tax Special Regulatory Order.",
    )


class UpdateProductResponse(ProductResponse):
    """
    Response model for updating an existing product.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this product.
        name (str): Name of the product or service.
        description (Optional[str]): Detailed description of the product.
        hs_code (str): Harmonized System code for the product.
        sale_type (SaleTypeEnum): Type of sale for this item.
        unit_price (NonNegativeFloat): Base unit price of the product.
        unit_of_measurement (str): Unit of measurement (e.g., 'pcs', 'kg', 'hours').
        tax_rate (str): Default tax rate percentage for this product.
        retail_price (Optional[NonNegativeFloat]): Retail selling price.
        sales_tax_applicable (Optional[NonNegativeFloat]): Sales tax applicable amount.
        sales_tax_withheld (Optional[NonNegativeFloat]): Sales tax withheld amount.
        extra_tax (Optional[NonNegativeFloat]): Additional extra tax amount.
        further_tax (Optional[NonNegativeFloat]): Further tax amount applicable.
        federal_advance_duty_payable (Optional[NonNegativeFloat]): Federal Advance Duty payable amount.
        sro_schedule_code (Optional[SroScheduleCodeEnum]): SRO schedule code for tax calculations.
        sro_serial_number (Optional[str]): Serial number from Sales Tax Special Regulatory Order.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class DeleteProductRequest(OptionalUserIDMixin, DeleteRequestMixin):
    """
    Request model for deleting a product.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    pass


class DeleteProductResponse(DeleteResponseMixin):
    """
    Response model for deleting a product.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass


# --------------------------------- HSCode ---------------------------------- #
class HSCodeResponse(TimestampMixin, HSCodeBase, IDMixin):
    """
    Response model for an HS code.

    Attributes:
        id (UUID): Unique identifier for the record.
        hs_code (str): The HS code identifier.
        units_of_measurement (List[str]): Units of measurement for the HS code.
        description (str): Description of what the HS code represents.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class HSCodeResponseList(SQLModel):
    """
    Response model for a list of HS codes.

    Attributes:
        data (List[HSCodeResponse]): List of HS code records.
    """

    data: List[HSCodeResponse] = Field(
        default=[], description="List of HS code records."
    )


class CreateHSCodeRequest(HSCodeBase):
    """
    Request model for creating a new HS code.

    Attributes:
        hs_code (str): The HS code identifier.
        description (str): Description of what the HS code represents.
    """

    pass


class CreateHSCodeResponse(HSCodeResponse):
    """
    Response model for creating a new HS code.

    Attributes:
        id (UUID): Unique identifier for the record.
        hs_code (str): The HS code identifier.
        units_of_measurement (List[str]): Units of measurement for the HS code.
        description (str): Description of what the HS code represents.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetHsCodeRequest(HSCodeBase, OptionalIDMixin):
    """
    Request model for retrieving a single HS code.

    Attributes:
        id (UUID): Unique identifier for the record.
        hs_code (Optional[str]): The HS code identifier.
        description (Optional[str]): Description of what the HS code represents.
    """

    pass


class GetHsCodeResponse(HSCodeResponse):
    """
    Response model for retrieving a single HS code.

    Attributes:
        id (UUID): Unique identifier for the record.
        hs_code (str): The HS code identifier.
        units_of_measurement (List[str]): Units of measurement for the HS code.
        description (str): Description of what the HS code represents.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetHSCodesRequest(
    OrderedRequestMixin[HSCodeFieldsEnum],
    PaginatedRequestMixin,
    HSCodeBase,
    OptionalIDMixin,
):
    """
    Request model for retrieving HS codes with filtering and pagination.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        hs_code (Optional[str]): The HS code identifier.
        units_of_measurement (Optional[List[str]]): Units of measurement for the HS code.
        description (Optional[str]): Description of what the HS code represents.
        page (int): Page number for pagination.
        page_size (int): Number of records per page for pagination.
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[HSCodeFieldsEnum]): Field to order by.
    """

    hs_code: Optional[str] = Field(  # type: ignore[override]
        default=None, description="The HS code identifier."
    )

    units_of_measurement: Optional[List[str]] = Field(  # type: ignore[override]
        default=None, description="Unit of measurement for the HS code."
    )

    description: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Description of what the HS code represents."
    )

    order_by: Optional[HSCodeFieldsEnum] = Field(  # type: ignore[override]
        default=None, description="Field to order by."
    )


class GetHSCodesResponse(PaginatedResponseMixin, HSCodeResponseList):
    """
    Response model for retrieving HS codes.

    Attributes:
        data (list[HSCodeResponse]): List of HS code records.
        total (int): Total number of records available.
        next_page (bool): Indicates if there is a next page.
    """

    pass


class UpdateHSCodeRequest(HSCodeBase, IDMixin):
    """
    Request model for updating an existing HS code.

    Attributes:
        id (UUID): Unique identifier for the record.
        hs_code (Optional[str]): The HS code identifier.
        units_of_measurement (Optional[List[str]]): Units of measurement for the HS code.
        description (Optional[str]): Description of what the HS code represents.
    """

    hs_code: Optional[str] = Field(  # type: ignore[override]
        default=None, description="The HS code identifier."
    )
    units_of_measurement: Optional[List[str]] = Field(  # type: ignore[override]
        default=None, description="Units of measurement for the HS code."
    )
    description: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Description of what the HS code represents."
    )


class UpdateHSCodeResponse(HSCodeResponse):
    """
    Response model for updating an existing HS code.

    Attributes:
        hs_code (str): The HS code identifier.
        units_of_measurement (List[str]): Units of measurement for the HS code.
        description (str): Description of what the HS code represents.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class DeleteHSCodeRequest(DeleteRequestMixin):
    """
    Request model for deleting an HS code.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
    """

    pass


class DeleteHSCodeResponse(DeleteResponseMixin):
    """
    Response model for deleting an HS code.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass
