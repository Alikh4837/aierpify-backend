# src\utils.py


from enum import Enum
from typing import Optional, Type
from uuid import UUID

from sqlmodel import SQLModel, asc, desc

from src.auth.user import AuthUser
from src.database import TQUERY
from src.enums import TENUM, OrderEnum
from src.exceptions import (
    BadRequestException,
    ForbiddenException,
    InternalServerErrorException,
)


def get_user_id(auth_user: AuthUser, user_id: Optional[UUID] = None) -> UUID:
    """
    Get the user ID from the authenticated user or the input user ID.

    Returns the provided user_id if the user is an admin.
    Or if the user_id matches the authenticated user's ID.
    Otherwise, returns the authenticated user's ID when user_id is not provided.

    Args:
        auth_user (AuthUser): The authenticated user object.
        user_id (Optional[UUID]): The user ID to validate. Defaults to None.

    Returns:
        UUID: The validated user ID.

    Raises:
        ForbiddenException: If the user_id is provided and does not match the authenticated user's ID,
                            and the authenticated user is not an admin.
        InternalServerErrorException: If unable to determine a valid user ID.
    """
    return_user_id = None

    # Check if the user_id exists
    if user_id:
        # Check if the user_id matches the authenticated user's ID
        if user_id == auth_user.user.id:
            return_user_id = auth_user.user.id

        # If the id does not match, only admins can access other users' data
        elif auth_user.user.role == "admin":
            return_user_id = user_id

        else:
            raise ForbiddenException(
                detail="Forbidden, User ID mismatch, Only Admins can access other users' data via user_id.",
            )

    # If user_id is not provided, return the authenticated user's ID
    else:
        return_user_id = auth_user.user.id

    if not return_user_id:
        raise InternalServerErrorException(
            message="Failed to determine user ID",
            detail="User ID could not be determined from the authenticated user or input.",
        )

    return return_user_id


def enforce_user_role(
    auth_user: AuthUser, required_role: str = "admin", detail: str = "Forbidden"
) -> None:
    """
    Enforce that the authenticated user has the required role.

    Args:
        auth_user (AuthUser): The authenticated user object.
        required_role (str): The required role to access the resource. Defaults to "admin".
        detail (str): Detail message for the exception if the role check fails. Defaults to "Forbidden".

    Raises:
        ForbiddenException: If the user does not have the required role.
    """
    if auth_user.user.role != required_role:
        raise ForbiddenException(
            message=f"Forbidden, User role '{auth_user.user.role}' does not have access, requires '{required_role}' role.",
            detail=detail,
        )


async def apply_ordering_sql(
    query: TQUERY,
    table: Type[SQLModel],
    order: Optional[OrderEnum] = None,
    order_by: Optional[TENUM] = None,
) -> TQUERY:
    """
    Apply ordering to a SQLModel Select statement based on the provided order and order_by parameters.
    This function is generic and can be used with any SQLModel table.

    Args:
        query: The SQLModel Select statement to apply ordering to.
        table: The SQLModel table class (e.g., Hero).
        order (Order, optional): The ordering direction (ASC or DESC).
        order_by (Union[str, Enum], optional): The field to order by. Can be a string
                                                representing the column name, or an Enum
                                                member whose value is the column name.
    Returns:
        The modified SQLModel Select statement with ordering applied (same type as input query).
    """
    column_name_str: str

    if not order_by:
        column_name_str = "created_at"
    elif isinstance(order_by, Enum):
        column_name_str = order_by.value
    elif isinstance(order_by, str):
        column_name_str = order_by
    else:
        raise BadRequestException(
            detail=f"Invalid type for order_by: {type(order_by)}. Must be a string or an Enum."
        )

    if not column_name_str:
        raise BadRequestException(detail="order_by must be a valid column name.")

    try:
        # Handle normally reserved keywords in SQLAlchemy
        if column_name_str in ["metadata"]:
            column_name_str = column_name_str + "_"

        order_column = getattr(table, column_name_str)

    except AttributeError:
        raise BadRequestException(
            detail=f"Column '{column_name_str}' does not exist in table {table.__name__}."
        )

    match order:
        case OrderEnum.DESC:
            query = query.order_by(desc(order_column))  # type: ignore

        case OrderEnum.ASC:
            query = query.order_by(asc(order_column))  # type: ignore

        case None:
            # Default ordering by created_at descending if no order is specified
            query = query.order_by(desc(order_column))  # type: ignore

        case _:
            raise BadRequestException(
                detail=f"Invalid order value: {order}. Must be 'asc' or 'desc'."
            )

    return query


async def apply_pagination_sql(
    query: TQUERY,
    page: int,
    page_size: int,
) -> TQUERY:
    """
    Apply pagination to a SQLModel Select statement based on the provided limit and offset parameters.
    This function is generic and can be used with any SQLModel table.

    Args:
        query: The SQLModel Select statement to apply pagination to.
        page (int): The page number (1-based index).
        page_size (int): The number of items per page.
    """

    offset = (page - 1) * page_size

    query = query.limit(page_size).offset(offset)
    return query
