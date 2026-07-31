# src\customers\service.py
from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import func
from sqlmodel import col, select

from src.auth.user import AuthUser
from src.customers.models import Customer
from src.customers.schemas import (
    CreateCustomerRequest,
    CreateCustomerResponse,
    CustomerResponse,
    DeleteCustomerRequest,
    DeleteCustomerResponse,
    GetCustomerRequest,
    GetCustomerResponse,
    GetCustomersRequest,
    GetCustomersResponse,
    UpdateCustomerRequest,
    UpdateCustomerResponse,
)
from src.exceptions import (
    NotFoundException,
)
from src.users.service import UserPlanService
from src.utils import apply_ordering_sql, apply_pagination_sql, get_user_id


# --------------------------------------------------------------------------- #
#                               CRUD Services                                 #
# --------------------------------------------------------------------------- #
class CustomerService:
    @staticmethod
    async def get_customer_single(
        auth_user: AuthUser, input_params: GetCustomerRequest
    ) -> GetCustomerResponse:
        """
        Fetch a single customer by ID ensuring ownership.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = (
            select(Customer)
            .where(Customer.user_id == user_id)
            .where(Customer.id == input_params.id)
        )
        response = await session.exec(stmt)
        data = response.first()

        if not data:
            raise NotFoundException(
                message="Customer not found",
                detail=f"No customer found with ID {input_params.id}",
                extra={"customer_id": str(input_params.id)},
            )

        return GetCustomerResponse.model_validate(data.model_dump())

    @staticmethod
    async def get_customers(
        auth_user: AuthUser, input_params: GetCustomersRequest
    ) -> GetCustomersResponse:
        """
        Retrieve customers owned by the authenticated user with filtering & pagination.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Filtering & pagination parameters.

        Returns:
            GetCustomerResponse: Paginated customer list.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        # Base ownership filter
        conditions: List[object] = [Customer.user_id == user_id]

        # Check if ID filter is applied
        if input_params.id:
            conditions.append(Customer.id == input_params.id)

        # If ID is provided, ignore other filters and fetch by ID only
        else:
            if input_params.name:
                # Case-insensitive partial match for name
                name_search = f"%{input_params.name.lower()}%"
                conditions.append(func.lower(Customer.name).like(name_search))

            if input_params.email:
                conditions.append(Customer.email == input_params.email)

            if input_params.phone:
                conditions.append(Customer.phone == input_params.phone)

            if input_params.province:
                conditions.append(Customer.province == input_params.province)

            if input_params.registration_type:
                conditions.append(
                    Customer.registration_type == input_params.registration_type
                )

            if input_params.national_tax_number:
                conditions.append(
                    Customer.national_tax_number == input_params.national_tax_number
                )

            if input_params.sales_tax_registration_number:
                conditions.append(
                    Customer.sales_tax_registration_number
                    == input_params.sales_tax_registration_number
                )

        page = input_params.page
        page_size = input_params.page_size

        # Count total
        count_stmt = select(func.count()).select_from(Customer).where(*conditions)  # type: ignore[arg-type]
        total_result = await session.exec(count_stmt)
        total = total_result.one()

        # Pagination
        stmt = (
            select(Customer).where(*conditions)  # type: ignore[arg-type]
        )

        # Apply pagination
        stmt = await apply_pagination_sql(stmt, page, page_size)

        # Apply ordering
        stmt = await apply_ordering_sql(
            stmt, Customer, input_params.order, input_params.order_by
        )

        result = await session.exec(stmt)
        rows: Sequence[Customer] = result.all()

        # Cast/validate to response models
        data: List[CustomerResponse] = [
            CustomerResponse.model_validate(r.model_dump()) for r in rows
        ]

        next_page = total > page * page_size
        return GetCustomersResponse(data=data, total=total, next_page=next_page)

    @staticmethod
    async def create_customer(
        auth_user: AuthUser, input_data: CreateCustomerRequest
    ) -> CreateCustomerResponse:
        """
        Create a new customer owned by the authenticated user.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Customer creation data.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        # Prepare payload
        payload = input_data.model_dump()
        payload["user_id"] = user_id

        # Queue the usage counter increment
        # This will be committed after the product is created
        await UserPlanService.increment_usage_counter(
            auth_user, counter_field="customers_used", increment_by=1
        )

        customer = Customer(**payload)
        session.add(customer)

        await session.commit()
        await session.refresh(customer)

        return CreateCustomerResponse.model_validate(customer.model_dump())

    @staticmethod
    async def update_customer(
        auth_user: AuthUser, input_data: UpdateCustomerRequest
    ) -> UpdateCustomerResponse:
        """
        Update an existing customer owned by the authenticated user.

        Args:
            auth_user: Authenticated user context containing DB session.
            customer_id: ID of the customer to update.
            input_data: Customer update data.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = (
            select(Customer)
            .where(Customer.user_id == user_id)
            .where(Customer.id == input_data.id)
        )
        result = await session.exec(stmt)
        customer = result.first()

        if not customer:
            raise NotFoundException(
                message="Customer not found",
                detail=f"No customer found with ID {input_data.id}",
                extra={"customer_id": str(input_data.id)},
            )

        customer_fields = Customer.model_fields.keys()
        for field in customer_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(customer, field, value)

        session.add(customer)
        await session.commit()
        await session.refresh(customer)

        return UpdateCustomerResponse.model_validate(customer.model_dump())

    @staticmethod
    async def delete_customers(
        auth_user: AuthUser, input_data: DeleteCustomerRequest
    ) -> DeleteCustomerResponse:
        """Bulk delete customers by IDs ensuring ownership."""

        session = auth_user.session
        ids = input_data.id
        user_id = get_user_id(auth_user)

        if not ids:
            return DeleteCustomerResponse(
                message="No customers specified for deletion", detail={"deleted": 0}
            )

        # Fetch customers to verify ownership
        stmt = (
            select(Customer)
            .where(col(Customer.user_id) == user_id)
            .where(col(Customer.id).in_(ids))
        )

        result = await session.exec(stmt)
        customers: List[Customer] = list(result.all())

        # Ownership & existence checks
        found_ids = {c.id for c in customers}
        missing_ids = [str(i) for i in ids if i not in found_ids]

        if missing_ids:
            raise NotFoundException(
                message="Some customers not found",
                detail="One or more customer IDs do not exist",
                extra={"missing_ids": missing_ids},
            )

        for customer in customers:
            await session.delete(customer)

        await session.commit()

        return DeleteCustomerResponse(
            message=f"Deleted {len(customers)} customers successfully",
            detail={"deleted": len(customers), "ids": [str(c.id) for c in customers]},
        )
