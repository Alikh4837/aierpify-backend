# src\products\service.py
from __future__ import annotations

from typing import List, Sequence
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, or_, select

from src.auth.user import AuthUser
from src.exceptions import (
    InternalServerErrorException,
    NotFoundException,
)
from src.fbr.schemas import FBRUOMRequest
from src.fbr.utils import get_fbr_uom
from src.products.models import HSCode, Product
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
    HSCodeResponse,
    ProductResponse,
    UpdateHSCodeRequest,
    UpdateHSCodeResponse,
    UpdateProductRequest,
    UpdateProductResponse,
)
from src.users.service import UserPlanService
from src.utils import (
    apply_ordering_sql,
    apply_pagination_sql,
    enforce_user_role,
    get_user_id,
)


# --------------------------------------------------------------------------- #
#                               CRUD Services                                 #
# --------------------------------------------------------------------------- #
class ProductService:
    @staticmethod
    async def get_product_single(
        auth_user: AuthUser, input_params: GetProductRequest
    ) -> GetProductResponse:
        """
        Fetch a single product by ID ensuring ownership.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)

        stmt = (
            select(Product)
            .where(Product.user_id == user_id)
            .where(Product.id == input_params.id)
        )
        response = await session.exec(stmt)
        data = response.first()

        if not data:
            raise NotFoundException(
                message="Product not found",
                detail=f"No product found with ID {input_params.id}",
                extra={"product_id": str(input_params.id)},
            )

        return GetProductResponse.model_validate(data.model_dump())

    @staticmethod
    async def get_products(
        auth_user: AuthUser, input_params: GetProductsRequest
    ) -> GetProductsResponse:
        """
        Retrieve products owned by the authenticated user with filtering & pagination.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Filtering & pagination parameters.

        Returns:
            GetProductsResponse: Paginated product list.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_params.user_id)
        # Pagination Flag
        apply_pagination: bool = True

        # Base ownership filter
        conditions: List[object] = [Product.user_id == user_id]

        # Check if ID filter is applied
        match input_params.id:
            case UUID():
                # If ID is provided, ignore other filters and fetch by ID only
                conditions.append(Product.id == input_params.id)
                apply_pagination = False  # Disable pagination for single record fetch
            case list() if len(input_params.id or []) > 0:
                # If a list of IDs is provided, filter by these IDs
                # Deduplicate IDs
                product_ids = list(set(input_params.id))
                conditions.append(col(Product.id).in_(product_ids))
                apply_pagination = False  # Disable pagination for specific record fetch
            case None:
                # If ID/IDs are not provided, apply other filters
                if input_params.name:
                    # Case-insensitive partial match for name
                    name_search = f"%{input_params.name.lower()}%"
                    conditions.append(func.lower(Product.name).like(name_search))

                if input_params.description:
                    # Case-insensitive partial match for description
                    desc_search = f"%{input_params.description.lower()}%"
                    conditions.append(func.lower(Product.description).like(desc_search))

                if input_params.hs_code:
                    conditions.append(Product.hs_code == input_params.hs_code)

                if input_params.sale_type:
                    conditions.append(Product.sale_type == input_params.sale_type)

                if input_params.unit_price is not None:
                    conditions.append(Product.unit_price == input_params.unit_price)

                if input_params.unit_of_measurement:
                    conditions.append(
                        Product.unit_of_measurement == input_params.unit_of_measurement
                    )

                if input_params.tax_rate:
                    conditions.append(Product.tax_rate == input_params.tax_rate)

                if input_params.retail_price is not None:
                    conditions.append(Product.retail_price == input_params.retail_price)

                if input_params.sro_schedule_code:
                    conditions.append(
                        Product.sro_schedule_code == input_params.sro_schedule_code
                    )

                if input_params.sro_serial_number:
                    conditions.append(
                        Product.sro_serial_number == input_params.sro_serial_number
                    )

        page = input_params.page
        page_size = input_params.page_size

        # Count total
        count_stmt = select(func.count()).select_from(Product).where(*conditions)  # type: ignore[arg-type]
        total_result = await session.exec(count_stmt)
        total = total_result.one()

        # Pagination
        stmt = (
            select(Product).where(*conditions)  # type: ignore[arg-type]
        )

        # Apply pagination
        if apply_pagination:
            stmt = await apply_pagination_sql(stmt, page, page_size)

        # Apply ordering
        stmt = await apply_ordering_sql(
            stmt, Product, input_params.order, input_params.order_by
        )

        result = await session.exec(stmt)
        rows: Sequence[Product] = result.all()

        # Cast/validate to response models
        data: List[ProductResponse] = [
            ProductResponse.model_validate(r.model_dump()) for r in rows
        ]

        next_page = total > page * page_size if apply_pagination else False
        return GetProductsResponse(data=data, total=total, next_page=next_page)

    @staticmethod
    async def get_products_by_ids(
        auth_user: AuthUser, product_ids: List[UUID]
    ) -> List[ProductResponse]:
        """
        Fetch multiple products by their IDs ensuring ownership.

        Args:
            auth_user: Authenticated user context containing DB session.
            product_ids: List of product IDs to fetch.

        Returns:
            List[ProductResponse]: List of product details.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user)

        stmt = (
            select(Product)
            .where(Product.user_id == user_id)
            .where(col(Product.id).in_(product_ids))
        )
        result = await session.exec(stmt)
        products: Sequence[Product] = result.all()

        return [ProductResponse.model_validate(p.model_dump()) for p in products]

    @staticmethod
    async def create_product(
        auth_user: AuthUser, input_data: CreateProductRequest
    ) -> CreateProductResponse:
        """
        Create a new product owned by the authenticated user.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Product creation data.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        # Prepare payload
        payload = input_data.model_dump()
        payload["user_id"] = user_id

        # Queue the usage counter increment
        # This will be committed after the product is created
        await UserPlanService.increment_usage_counter(
            auth_user, counter_field="products_used", increment_by=1
        )

        product = Product(**payload)
        session.add(product)

        await session.commit()
        await session.refresh(product)

        return CreateProductResponse.model_validate(product.model_dump())

    @staticmethod
    async def update_product(
        auth_user: AuthUser, input_data: UpdateProductRequest
    ) -> UpdateProductResponse:
        """
        Update an existing product owned by the authenticated user.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: Product update data.
        """

        session = auth_user.session
        user_id = get_user_id(auth_user, input_data.user_id)

        stmt = (
            select(Product)
            .where(Product.user_id == user_id)
            .where(Product.id == input_data.id)
        )
        result = await session.exec(stmt)
        product = result.first()

        if not product:
            raise NotFoundException(
                message="Product not found",
                detail=f"No product found with ID {input_data.id}",
                extra={"product_id": str(input_data.id)},
            )

        product_fields = Product.model_fields.keys()
        for field in product_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(product, field, value)

        session.add(product)
        await session.commit()
        await session.refresh(product)

        return UpdateProductResponse.model_validate(product.model_dump())

    @staticmethod
    async def delete_products(
        auth_user: AuthUser, input_data: DeleteProductRequest
    ) -> DeleteProductResponse:
        """Bulk delete products by IDs ensuring ownership."""

        session = auth_user.session
        ids = input_data.id
        user_id = get_user_id(auth_user)

        if not ids:
            return DeleteProductResponse(
                message="No products specified for deletion", detail={"deleted": 0}
            )

        # Fetch products to verify ownership
        stmt = (
            select(Product)
            .where(col(Product.user_id) == user_id)
            .where(col(Product.id).in_(ids))
        )

        result = await session.exec(stmt)
        products: List[Product] = list(result.all())

        # Ownership & existence checks
        found_ids = {p.id for p in products}
        missing_ids = [str(i) for i in ids if i not in found_ids]

        if missing_ids:
            raise NotFoundException(
                message="Some products not found",
                detail="One or more product IDs do not exist",
                extra={"missing_ids": missing_ids},
            )

        for product in products:
            await session.delete(product)

        await session.commit()

        return DeleteProductResponse(
            message=f"Deleted {len(products)} products successfully",
            detail={"deleted": len(products), "ids": [str(p.id) for p in products]},
        )


class HSCodeService:
    @staticmethod
    async def get_hs_code_single(
        auth_user: AuthUser, input_params: GetHsCodeRequest
    ) -> GetHsCodeResponse:
        """
        Fetch a single HS code by ID ensuring ownership.
        """

        session = auth_user.session

        stmt = select(HSCode)

        if input_params.id:
            stmt = stmt.where(HSCode.id == input_params.id)

        if input_params.hs_code:
            stmt = stmt.where(HSCode.hs_code == input_params.hs_code)

        if input_params.units_of_measurement:
            stmt = stmt.where(
                HSCode.units_of_measurement == input_params.units_of_measurement
            )

        if input_params.description:
            # Case-insensitive partial match for description
            description_search = f"%{input_params.description.lower()}%"
            stmt = stmt.where(func.lower(HSCode.description).like(description_search))

        response = await session.exec(stmt)
        data = response.first()

        if not data:
            raise NotFoundException(
                message="HS Code not found",
                detail="No HS Code found matching the criteria",
                extra={"hs_code": str(input_params.hs_code or input_params.id)},
            )

        return GetHsCodeResponse.model_validate(data.model_dump())

    @staticmethod
    async def get_hs_codes(
        auth_user: AuthUser, input_params: GetHSCodesRequest
    ) -> GetHSCodesResponse:
        """
        Retrieve HS codes with filtering & pagination.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_params: Filtering & pagination parameters.

        Returns:
            GetHSCodeResponse: Paginated HS code list.
        """

        session = auth_user.session

        # Base conditions
        conditions: List[object] = []

        # Check if ID filter is applied
        if input_params.id:
            conditions.append(HSCode.id == input_params.id)

        # If ID is provided, ignore other filters and fetch by ID only
        else:
            if input_params.hs_code:
                conditions.append(HSCode.hs_code == input_params.hs_code)

            if input_params.units_of_measurement:
                conditions.append(
                    or_(
                        *[
                            col(HSCode.units_of_measurement).contains([value])
                            for value in input_params.units_of_measurement
                        ]
                    )
                )

            if input_params.description:
                # Case-insensitive partial match for description
                desc_search = f"%{input_params.description.lower()}%"
                conditions.append(func.lower(HSCode.description).like(desc_search))

        page = input_params.page
        page_size = input_params.page_size

        # Count total
        count_stmt = select(func.count()).select_from(HSCode).where(*conditions)  # type: ignore[arg-type]
        total_result = await session.exec(count_stmt)
        total = total_result.one()

        # Pagination
        stmt = (
            select(HSCode).where(*conditions)  # type: ignore[arg-type]
        )

        # Apply pagination
        stmt = await apply_pagination_sql(stmt, page, page_size)

        # Apply ordering
        stmt = await apply_ordering_sql(
            stmt, HSCode, input_params.order, input_params.order_by
        )

        result = await session.exec(stmt)
        rows: Sequence[HSCode] = result.all()

        # Cast/validate to response models
        data: List[HSCodeResponse] = [
            HSCodeResponse.model_validate(r.model_dump()) for r in rows
        ]

        next_page = total > page * page_size
        return GetHSCodesResponse(data=data, total=total, next_page=next_page)

    @staticmethod
    async def get_all_hs_codes(auth_user: AuthUser) -> GetHSCodesResponse:
        """
        Retrieve all HS codes without pagination.

        Args:
            auth_user: Authenticated user context containing DB session.

        Returns:
            List[HSCodeResponse]: List of all HS codes.
        """

        session = auth_user.session

        stmt = select(HSCode)

        result = await session.exec(stmt)
        rows = result.all()

        # Cast/validate to response models
        data: List[HSCodeResponse] = [
            HSCodeResponse.model_validate(r.model_dump()) for r in rows
        ]

        return GetHSCodesResponse(data=data, total=len(data), next_page=False)

    @staticmethod
    async def create_hs_code(
        auth_user: AuthUser, input_data: CreateHSCodeRequest
    ) -> CreateHSCodeResponse:
        """
        Create a new HS code.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: HS code creation data.
        """

        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        # Prepare payload
        payload = input_data.model_dump()

        hs_code = HSCode(**payload)

        # Fetch UOM from FBR if not provided
        if not input_data.units_of_measurement:
            # TODO: Fix the circular import issue to enable this feature
            try:
                uom_response = await get_fbr_uom(
                    auth_user, FBRUOMRequest(hs_code=hs_code.hs_code, annexure_id="3")
                )

                if (
                    uom_response.units_of_measurement
                    and not len(uom_response.units_of_measurement) == 0
                ):
                    hs_code.units_of_measurement = uom_response.units_of_measurement

                else:
                    hs_code.units_of_measurement = [""]

            except Exception as e:
                raise InternalServerErrorException(
                    message="Failed to retrieve UOM from FBR",
                    detail=str(e),
                    extra={
                        "operation": "create_hs_code",
                        "user_id": str(auth_user.user.id),
                    },
                )

        session.add(hs_code)
        await session.commit()
        await session.refresh(hs_code)

        return CreateHSCodeResponse.model_validate(hs_code.model_dump())

    @staticmethod
    async def update_hs_code(
        auth_user: AuthUser, input_data: UpdateHSCodeRequest
    ) -> UpdateHSCodeResponse:
        """
        Update an existing HS code.

        Args:
            auth_user: Authenticated user context containing DB session.
            input_data: HS code update data.
        """

        enforce_user_role(auth_user, "admin")

        session = auth_user.session

        stmt = select(HSCode).where(HSCode.id == input_data.id)
        result = await session.exec(stmt)
        hs_code = result.first()

        if not hs_code:
            raise NotFoundException(
                message="HS code not found",
                detail=f"No HS code found with ID {input_data.id}",
                extra={"hs_code_id": str(input_data.id)},
            )

        hs_code_fields = HSCode.model_fields.keys()
        for field in hs_code_fields:
            value = getattr(input_data, field, None)
            if value is not None:
                setattr(hs_code, field, value)

        session.add(hs_code)
        await session.commit()
        await session.refresh(hs_code)

        return UpdateHSCodeResponse.model_validate(hs_code.model_dump())

    @staticmethod
    async def delete_hs_codes(
        auth_user: AuthUser, input_data: DeleteHSCodeRequest
    ) -> DeleteHSCodeResponse:
        """Bulk delete HS codes by IDs."""

        enforce_user_role(auth_user, "admin")

        session = auth_user.session
        ids = input_data.id

        if not ids:
            return DeleteHSCodeResponse(
                message="No HS codes specified for deletion", detail={"deleted": 0}
            )

        # Fetch HS codes
        stmt = select(HSCode).where(col(HSCode.id).in_(ids))

        result = await session.exec(stmt)
        hs_codes: List[HSCode] = list(result.all())

        # Existence checks
        found_ids = {h.id for h in hs_codes}
        missing_ids = [str(i) for i in ids if i not in found_ids]

        if missing_ids:
            raise NotFoundException(
                message="Some HS codes not found",
                detail="One or more HS code IDs do not exist",
                extra={"missing_ids": missing_ids},
            )

        for hs_code in hs_codes:
            await session.delete(hs_code)

        await session.commit()

        return DeleteHSCodeResponse(
            message=f"Deleted {len(hs_codes)} HS codes successfully",
            detail={"deleted": len(hs_codes), "ids": [str(h.id) for h in hs_codes]},
        )
