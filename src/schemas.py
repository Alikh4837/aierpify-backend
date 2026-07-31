# src\schemas.py
from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import declared_attr
from sqlmodel import Column, DateTime, Field, SQLModel, func

from src.enums import TENUM, OrderEnum


# ------------------------------ DB Model Mixins ----------------------------- #
class CreatedAtMixin:
    @declared_attr
    def created_at(self):  # type: ignore
        return Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )


class UpdatedAtMixin:
    @declared_attr
    def updated_at(self):  # type: ignore
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class AuthCreatedAtMixin:
    @declared_attr
    def created_at(self):  # type: ignore
        return Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )


class AuthUpdatedAtMixin:
    @declared_attr
    def updated_at(self):  # type: ignore
        return Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


# ----------------------------- I/O Model Mixins ----------------------------- #
class IDMixin(SQLModel):
    """
    Mixin for models with an ID field.

    Attributes:
        id (UUID): Unique identifier for the record.
    """

    id: UUID = Field(
        primary_key=True,
        description="Unique identifier for the record.",
    )


class OptionalIDMixin(SQLModel):
    """
    Mixin for models with an optional ID field.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
    """

    id: Optional[UUID] = Field(
        default=None, description="Unique identifier for the record."
    )


class OptionalIDListMixin(SQLModel):
    """
    Mixin for models with one or more optional IDs.

    Attributes:
        id (Optional[Union[List[UUID], UUID]]): Single or List of unique identifiers for the records.
    """

    id: Optional[Union[List[UUID], UUID]] = Field(
        default=None, description="List of unique identifiers for the records."
    )


class OptionalUserIDMixin(SQLModel):
    """
    Mixin for models with an optional user ID field.

    Attributes:
        user_id (Optional[UUID]): Unique identifier for the user.
    """

    user_id: Optional[UUID] = Field(
        default=None, description="Unique identifier for the user."
    )


class TimestampMixin(SQLModel):
    """
    Mixin for models with timestamp fields.

    Attributes:
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Timestamp when the record was created.",
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Timestamp when the record was last updated.",
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"onupdate": func.now(), "server_default": func.now()},
    )


class PaginatedRequestMixin(SQLModel):
    """
    Mixin for pagination request models.

    Attributes:
        page (int): Page number for pagination (default is 1).
        page_size (int): Number of items per page (default is 10).
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination (default is 1).",
    )
    page_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of items per page (default is 10).",
    )


class PaginatedResponseMixin(SQLModel):
    """
    Mixin for pagination response models.

    Attributes:
        total (int): Total number of items available.
        next_page (bool): Indicates if there is a next page.
    """

    total: int = Field(..., description="Total number of items available.")
    next_page: bool = Field(..., description="Indicates if there is a next page.")


class OrderedRequestMixin(SQLModel, Generic[TENUM]):
    """
    Mixin for models with ordering fields.

    Parameters:
        TENUM: Type variable for the field to order by. (Enum type)

    Attributes:
        order (Optional[OrderEnum]): Direction of ordering ('asc' or 'desc').
        order_by (Optional[TENUM]): Field to order by.
    """

    order: Optional[OrderEnum] = Field(
        default=OrderEnum.DESC,
        description="Direction of ordering ('asc' or 'desc').",
    )
    order_by: Optional[TENUM] = Field(default=None, description="Field to order by.")


class DeleteRequestMixin(SQLModel):
    """
    Mixin for delete request models.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
    """

    id: List[UUID] = Field(
        ...,
        description="Unique identifiers for the records to be deleted.",
        min_items=1,
        max_items=100,
        unique_items=True,
    )


class DeleteResponseMixin(SQLModel):
    """
    Mixin for delete response models.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    message: str = Field(..., description="Message about the deletion.")
    detail: Optional[Any] = Field(
        default=None, description="Additional detail about the deletion."
    )
