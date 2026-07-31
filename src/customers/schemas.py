from typing import List, Optional
from uuid import UUID

from sqlmodel import AutoString, Column, Field, SQLModel

from src.customers.enums import CustomerFieldsEnum, RegistrationTypeEnum
from src.enums import ProvinceEnum
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


# ---------------------------------------------------------------------------- #
#                                 Base Schemas                                 #
# ---------------------------------------------------------------------------- #
class CustomerBase(SQLModel):
    """
    A customer record for invoicing and business operations.

    Attributes:
        user_id (UUID): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
    """

    __tablename__ = "customers"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the user who owns this customer.",
    )
    name: str = Field(
        nullable=False,
        description="Full name or business name of the customer.",
    )
    email: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Primary email address of the customer.",
    )
    phone: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Contact phone number of the customer.",
    )
    address: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Physical address of the customer.",
    )
    province: Optional[ProvinceEnum] = Field(
        default=None,
        description="Province where the buyer is located.",
        sa_column=Column("province", AutoString, nullable=True),
    )
    registration_type: Optional[RegistrationTypeEnum] = Field(
        default=None,
        description="Type of business registration.",
        sa_column=Column("registration_type", AutoString, nullable=True),
    )
    national_tax_number: Optional[str] = Field(
        default=None,
        nullable=True,
        description="National Tax Number (NTN) for tax purposes.",
    )
    sales_tax_registration_number: Optional[str] = Field(
        default=None, nullable=True, description="Sales Tax Registration Number (STRN)."
    )


# ---------------------------------------------------------------------------- #
#                             Endpoint I/O Schemas                             #
# ---------------------------------------------------------------------------- #
# --------------------------------- Customer --------------------------------- #
class CustomerResponse(TimestampMixin, CustomerBase, IDMixin):
    """
    A customer record for invoicing and business operations.

    Attributes:
        id (UUID): Unique identifier for the customer.
        user_id (UUID): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class CustomerResponseList(SQLModel):
    """
    Response model for a list of customers.

    Attributes:
        data (List[CustomerResponse]): List of customer records.
    """

    data: List[CustomerResponse] = Field(
        default=[], description="List of customer records."
    )


class CreateCustomerRequest(CustomerBase):
    """
    Request model for creating a new customer.

    Attributes:
        user_id (Optional[UUID]): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user who owns this customer."
    )


class CreateCustomerResponse(CustomerResponse):
    """
    Response model for creating a new customer.

    Attributes:
        user_id (UUID): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).

    """

    pass


class GetCustomerRequest(OptionalUserIDMixin, IDMixin):
    """
    Request model for retrieving a single customer by ID.

    Attributes:
        id (UUID): Unique identifier for the customer.
        user_id (Optional[UUID]): ID of the user who owns this customer.
    """

    pass


class GetCustomerResponse(CustomerResponse):
    """
    Response model for retrieving a single customer by ID.

    Attributes:
        id (UUID): Unique identifier for the customer.
        user_id (UUID): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetCustomersRequest(
    OrderedRequestMixin[CustomerFieldsEnum],
    PaginatedRequestMixin,
    CustomerBase,
    OptionalIDMixin,
):
    """
    Request model for retrieving a user profile with filtering, pagination, and ordering.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who owns this customer.
        name (Optional[str]): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
        page (int): Page number for pagination.
        page_size (int): Number of items per page.
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[CustomerFieldsEnum]): Field to order the results by.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this profile belongs to."
    )

    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the user's business."
    )

    order_by: Optional[CustomerFieldsEnum] = Field(
        default=CustomerFieldsEnum.CREATED_AT,
        description="Field to order the results by.",
    )


class GetCustomersResponse(PaginatedResponseMixin, CustomerResponseList):
    """
    Response model for retrieving user profiles.

    Attributes:
        data (list[CustomerResponse]): List of customer records.
        total (int): Total number of records available.
        next_page (bool): Indicates if there is a next page.
    """

    pass


class UpdateCustomerRequest(CustomerBase, IDMixin):
    """
    Request model for updating an existing user profile.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user who owns this customer.
        name (Optional[str]): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this profile belongs to."
    )
    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the user's business."
    )


class UpdateCustomerResponse(CustomerResponse):
    """
    Response model for updating an existing user profile.

    Attributes:
        user_id (UUID): ID of the user who owns this customer.
        name (str): Full name or business name of the customer.
        email (Optional[str]): Primary email address of the customer.
        phone (Optional[str]): Contact phone number of the customer.
        address (Optional[str]): Physical address of the customer.
        province (Optional[ProvinceEnum]): Province where the buyer is located.
        registration_type (Optional[RegistrationTypeEnum]): Type of business registration.
        national_tax_number (Optional[str]): National Tax Number (NTN) for tax purposes.
        sales_tax_registration_number (Optional[str]): Sales Tax Registration Number (STRN).
    """

    pass


class DeleteCustomerRequest(OptionalUserIDMixin, DeleteRequestMixin):
    """
    Request model for deleting a user profile.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    pass


class DeleteCustomerResponse(DeleteResponseMixin):
    """
    Response model for deleting a user profile.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass
