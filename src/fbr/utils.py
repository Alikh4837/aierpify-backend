# src\fbr\utils.py

import json
import re
from copy import deepcopy
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx

from src.auth.user import AuthUser
from src.config import get_setting
from src.enums import SaleTypeEnum
from src.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from src.fbr.enums import FBRIntegrationScenarioEnum
from src.fbr.schemas import (
    FBRInvoice,
    FBRInvoiceItem,
    FBRItemError,
    FBRParsedResponse,
    FBRUOMRequest,
    FBRUOMResponse,
    ScenarioDefinition,
    ScenarioPayload,
)
from src.invoices.schemas import (
    InvoiceCompleteResponse,
    InvoiceItemResponse,
)
from src.products.enums import NumericTaxRateEnum, SpecialTaxRateEnum
from src.products.schemas import ProductResponse


# ---------------------------------------------------------------------------- #
#                            FBR Endpoint Functions                            #
# ---------------------------------------------------------------------------- #
async def send_fbr_request(
    *,
    url: str,
    token: str,
    payload: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Send an HTTP POST request to the FBR API.

    Args:
        url: Target FBR endpoint URL.
        token: Bearer token for authentication.
        payload: JSON-serializable body to send.

    Returns:
        httpx.Response: Raw HTTP response from the FBR service.

    Raises:
        InternalServerErrorException: If the HTTP request fails before receiving a response.
    """

    if not payload and not query_params:
        raise BadRequestException(
            message="FBR request payload and query parameters cannot both be empty",
            detail="Either payload or query_params must be provided to send_fbr_request.",
            extra={"url": url},
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Aierpify-Backend/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=100.0) as client:
            response = await client.post(
                url, json=payload, params=query_params, headers=headers
            )
    except httpx.HTTPError as exc:  # pragma: no cover - network error handling
        raise InternalServerErrorException(
            message="Failed to communicate with FBR API",
            detail=str(exc),
            extra={"url": url},
        ) from exc

    if get_setting("DEBUG", default=False, raise_error=False):
        print(f"FBR Request Payload:\n{json.dumps(payload, indent=2)}")
        try:
            response_content = response.json()
            print(f"FBR Response JSON:\n{json.dumps(response_content, indent=2)}")
        except json.JSONDecodeError:
            print(f"FBR Response Text:\n{response.text}")

    return response


async def get_fbr_request(
    *,
    url: str,
    token: str,
    query_params: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Send an HTTP GET request to the FBR API.

    Args:
        url: Target FBR endpoint URL.
        token: Bearer token for authentication.
        payload: JSON-serializable body to send.

    Returns:
        httpx.Response: Raw HTTP response from the FBR service.

    Raises:
        InternalServerErrorException: If the HTTP request fails before receiving a response.
    """

    if not query_params:
        raise BadRequestException(
            message="FBR request query parameters cannot be empty",
            detail="query_params must be provided to get_fbr_request.",
            extra={"url": url},
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Aierpify-Backend/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=100.0) as client:
            response = await client.get(url, params=query_params, headers=headers)
    except httpx.HTTPError as exc:  # pragma: no cover - network error handling
        raise InternalServerErrorException(
            message="Failed to communicate with FBR API",
            detail=str(exc),
            extra={"url": url},
        ) from exc

    return response


def parse_fbr_response(response: httpx.Response) -> FBRParsedResponse:
    """
    Normalize an HTTP response from the FBR API.

    Parses both top-level validation status and individual item errors,
    extracting all relevant error messages and reference numbers.

    Args:
        response: Raw HTTP response returned by the FBR endpoint.

    Returns:
        FBRParsedResponse: Normalized response with detailed error information.
    """
    payload: Optional[Dict[str, Any]] = None

    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = {}

    # HTTP status in the format HTTP_XXX
    http_status = f"HTTP_{response.status_code}"

    # Handle non-successful HTTP responses
    if not response.is_success:
        # Try to extract any error messages from payload
        error_messages = []
        if payload:
            validation = payload.get("validationResponse", {})
            if validation.get("error"):
                error_messages.append(str(validation["error"]))

            # Check for item-level errors
            invoice_statuses = validation.get("invoiceStatuses", [])
            if isinstance(invoice_statuses, list):
                for status in invoice_statuses:
                    if isinstance(status, dict) and status.get("error"):
                        error_messages.append(str(status["error"]))

        error_message = (
            ", ".join(error_messages)
            if error_messages
            else f"FBR API returned error {response.status_code}."
        )

        return FBRParsedResponse(
            success=False,
            status=http_status,
            message=error_message,
            error=error_message,
            item_errors=[],
            reference=None,
            response_body=payload,
        )

    # Parse successful HTTP response
    validation = (payload or {}).get("validationResponse") or {}

    # Extract top-level validation info
    validation_status = str(validation.get("status", "Unknown"))
    top_level_error = validation.get("error", "")
    top_level_error = str(top_level_error) if top_level_error else None

    # Parse individual item errors
    item_errors: List[FBRItemError] = []
    invoice_statuses = validation.get("invoiceStatuses", [])

    if isinstance(invoice_statuses, list):
        for item_status in invoice_statuses:
            if isinstance(item_status, dict):
                error_msg = item_status.get("error")
                item_no = item_status.get("itemSNo")

                # Only add if there's an actual error message
                if error_msg and item_no:
                    item_errors.append(
                        FBRItemError(item_no=str(item_no), error=str(error_msg))
                    )

    # Determine overall success
    is_valid = validation_status.lower() == "valid"

    # Extract reference number if available
    reference: Optional[str] = None
    if payload:
        reference = payload.get("invoiceNumber", None)

    # Build comprehensive message
    if is_valid:
        message = "Payload successfully processed by FBR."
    else:
        error_parts = []

        if top_level_error:
            error_parts.append(top_level_error)

        # Add item-level errors
        for item_error in item_errors:
            error_parts.append(f"Item {item_error.item_no}: {item_error.error}")

        message = "; ".join(error_parts) if error_parts else "FBR validation failed."

    return FBRParsedResponse(
        success=is_valid,
        status=http_status,
        message=message,
        error=top_level_error,
        item_errors=item_errors,
        reference=reference,
        response_body=payload,
    )


# ---------------------------------------------------------------------------- #
#                         FBR Invoice Builder Functions                        #
# ---------------------------------------------------------------------------- #
def find_product_by_id(
    product_id: UUID,
    products: List[ProductResponse],
) -> ProductResponse:
    # Get matching products for this item
    matching_products = [p for p in products if p.id == product_id]

    # Validate exactly one product found
    if len(matching_products) == 0:
        raise NotFoundException(
            f"No product found for item with product_id: {product_id}"
        )
    if len(matching_products) > 1:
        raise NotFoundException(
            f"Multiple products found for product_id: {product_id}. Expected exactly one."
        )

    product = matching_products[0]

    return product


def round_decimal(value: Decimal) -> Decimal:
    """Round a Decimal value to 2 decimal places using ROUND_HALF_UP.

    Args:
        value: Decimal value to round.

    Returns:
        Decimal: Rounded value with 2 decimal places.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sanitize_string_for_fbr(value: Optional[str]) -> str:
    """
    Make product descriptions safe for the FBR parser.

    FBR appears to reject payloads when a product description introduces a
    backslash in the serialized JSON body, most commonly through escaped double
    quotes. To avoid that, replace double quotes before serialization and remove
    literal backslashes from the source text.

    Args:
        value: Raw product description.

    Returns:
        str: Product description formatted for FBR.
    """

    if not value:
        return ""

    sanitized_value = value.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    sanitized_value = sanitized_value.replace("\\", " ")
    sanitized_value = sanitized_value.replace('"', "''")
    sanitized_value = re.sub(r"\s+", " ", sanitized_value).strip()

    return sanitized_value


def build_fbr_invoice_item(
    item: InvoiceItemResponse,
    product: ProductResponse,
    per_item_extra_tax: Decimal,
    per_item_further_tax: Decimal,
    per_item_fed_payable: Decimal,
) -> FBRInvoiceItem:
    """
    Convert an invoice item and its associated product into the FBR invoice item format.

    Args:
        item: Invoice item data.
        product: Product data associated with the invoice item.
        per_item_extra_tax: Invoice-level extra tax allocation per item.
        per_item_further_tax: Invoice-level further tax allocation per item.
        per_item_fed_payable: Invoice-level federal advance duty allocation per item.

    Returns:
        FBRInvoiceItem: Structured line item for the payload.
    """
    # Calculate / Process all fields
    hs_code = product.hs_code
    product_description = sanitize_string_for_fbr(product.name)
    tax_rate: str = ""
    tax_rate_decimal: Decimal = Decimal("0")

    match product.tax_rate:
        # If the tax rate is numeric, format as percentage string
        case NumericTaxRateEnum() as rate:
            tax_rate = f"{str(rate.value)}%"
            tax_rate_decimal = Decimal(str(rate.value))

        # If the tax rate is special, use its string value directly
        case SpecialTaxRateEnum() as special_rate:
            tax_rate = str(special_rate.value)
            tax_rate_decimal = Decimal("0")

        # Fallback to default tax rate percentage string
        case _:
            tax_rate = str(NumericTaxRateEnum._18.value) + "%"
            tax_rate_decimal = Decimal(str(NumericTaxRateEnum._18.value))

    unit_of_measurement = product.unit_of_measurement
    sale_type = item.sale_type or SaleTypeEnum.GOODS_STANDARD_RATE
    sale_type_str = str(sale_type.value)

    # Convert to Decimal and round immediately
    quantity_dec = round_decimal(Decimal(str(item.quantity)))
    discount_percentage_dec = round_decimal(Decimal(str(item.discount_percentage)))

    # Determine item price based on sale type and round
    price_dec: Decimal
    match sale_type:
        case SaleTypeEnum.THIRD_SCHEDULE_GOODS:
            price_dec = round_decimal(Decimal(str(item.retail_price or 0.00)))
        case _:
            price_dec = round_decimal(Decimal(str(item.unit_price or 0.00)))

    # Calculate totals using rounded Decimal values
    item_subtotal_dec = round_decimal(price_dec * quantity_dec)
    discount_dec = round_decimal(
        item_subtotal_dec * (discount_percentage_dec / Decimal("100"))
    )
    value_sales_excluding_st_dec = round_decimal(
        max(item_subtotal_dec - discount_dec, Decimal("0"))
    )

    # Calculate sales tax applicable based on tax rate
    sales_tax_applicable_dec: Decimal
    match sale_type:
        case SaleTypeEnum.EXEMPT_GOODS | SaleTypeEnum.GOODS_ZERO_RATE:
            sales_tax_applicable_dec = Decimal("0")
        case _:
            # Calculate sales tax: value_sales_excluding_st * (tax_rate / 100)
            sales_tax_applicable_dec = round_decimal(
                value_sales_excluding_st_dec * (tax_rate_decimal / Decimal("100"))
            )

    # Calculate total value
    total_value_dec = round_decimal(
        value_sales_excluding_st_dec + sales_tax_applicable_dec
    )

    # Calculate other tax components with rounding
    sales_tax_withheld_dec = round_decimal(
        round_decimal(Decimal(str(product.sales_tax_withheld or 0))) * quantity_dec
    )
    extra_tax_dec = round_decimal(
        round_decimal(Decimal(str(product.extra_tax or 0))) * quantity_dec
    )
    further_tax_dec = round_decimal(
        round_decimal(Decimal(str(product.further_tax or 0))) * quantity_dec
    )
    fed_payable_dec = round_decimal(
        round_decimal(Decimal(str(product.federal_advance_duty_payable or 0)))
        * quantity_dec
    )
    extra_tax_dec = round_decimal(extra_tax_dec + per_item_extra_tax)
    further_tax_dec = round_decimal(further_tax_dec + per_item_further_tax)
    fed_payable_dec = round_decimal(fed_payable_dec + per_item_fed_payable)
    retail_price_dec = round_decimal(Decimal(str(item.retail_price or 0.00)))

    # Convert to float for response
    quantity = float(quantity_dec)
    total_value = float(total_value_dec)
    value_sales_excluding_st = float(value_sales_excluding_st_dec)
    retail_price = float(retail_price_dec)
    sales_tax_applicable = float(sales_tax_applicable_dec)
    sales_tax_withheld = float(sales_tax_withheld_dec)
    extra_tax = float(extra_tax_dec)
    further_tax = float(further_tax_dec)
    fed_payable = float(fed_payable_dec)
    discount = float(discount_dec)

    sro_schedule_no = (
        str(product.sro_schedule_code.value) if product.sro_schedule_code else ""
    )
    sro_item_serial_no = product.sro_serial_number or ""

    invoice_item: FBRInvoiceItem = FBRInvoiceItem(
        hsCode=hs_code,
        productDescription=product_description,
        rate=tax_rate,
        uoM=unit_of_measurement,
        quantity=quantity,
        totalValues=total_value,
        valueSalesExcludingST=value_sales_excluding_st,
        fixedNotifiedValueOrRetailPrice=retail_price,
        salesTaxApplicable=sales_tax_applicable,
        salesTaxWithheldAtSource=sales_tax_withheld,
        extraTax=extra_tax,
        furtherTax=further_tax,
        fedPayable=fed_payable,
        discount=discount,
        saleType=sale_type_str,
        sroScheduleNo=sro_schedule_no,
        sroItemSerialNo=sro_item_serial_no,
    )

    return invoice_item


def build_fbr_invoice(
    data: InvoiceCompleteResponse,
) -> FBRInvoice:
    """Construct the JSON body expected by the FBR invoice endpoints.

    Args:
        invoice: Invoice database model.
        customer: Customer associated with the invoice.
        items: Sequence of invoice item contexts joined with their products.
        seller_profile: Seller profile information.
        fbr_profile: FBR configuration and tokens for the seller.

    Returns:
        Dict[str, Any]: Structured payload ready for serialization.
    """

    # Invoice data
    customer = data.customer
    products = data.products
    invoice_items = data.items

    # Profiles
    fbr_profile = data.fbr_profile
    user_profile = data.user_profile

    item_count = len(invoice_items)
    invoice_extra_tax_total = round_decimal(Decimal(str(data.extra_tax_amount or 0)))
    invoice_further_tax_total = round_decimal(
        Decimal(str(data.further_tax_amount or 0))
    )
    invoice_fed_payable_total = round_decimal(
        Decimal(str(data.federal_advance_duty_payable_amount or 0))
    )
    if item_count > 0:
        per_item_extra_tax = round_decimal(invoice_extra_tax_total / item_count)
        per_item_further_tax = round_decimal(invoice_further_tax_total / item_count)
        per_item_fed_payable = round_decimal(invoice_fed_payable_total / item_count)
    else:
        per_item_extra_tax = Decimal("0")
        per_item_further_tax = Decimal("0")
        per_item_fed_payable = Decimal("0")

    fbr_invoice_items: List[FBRInvoiceItem] = []
    for item in invoice_items:
        product = find_product_by_id(item.product_id, products)
        line_item = build_fbr_invoice_item(
            item,
            product,
            per_item_extra_tax,
            per_item_further_tax,
            per_item_fed_payable,
        )
        fbr_invoice_items.append(line_item)

    invoice_type = str(data.invoice_type.value) if data.invoice_type else "Sale Invoice"
    issue_date = (
        datetime.strptime(
            data.issue_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"
        )
        .astimezone(tz=ZoneInfo("Asia/Karachi"))
        .strftime("%Y-%m-%d")
    )
    invoice_number = data.invoice_number
    national_tax_number = fbr_profile.national_tax_number or ""
    seller_business_name = user_profile.name or ""
    seller_province = str(user_profile.province.value) if user_profile.province else ""
    seller_address = sanitize_string_for_fbr(user_profile.address)

    customer_national_tax_number = customer.national_tax_number or ""
    customer_address = sanitize_string_for_fbr(customer.address)
    customer_province = str(customer.province.value) if customer.province else ""
    customer_registration_type = (
        str(customer.registration_type.value)
        if customer.registration_type
        else "Registered"
    )

    payload: FBRInvoice = FBRInvoice(
        sourceInvoiceNo=invoice_number,
        invoiceRefNo=invoice_number,
        invoiceType=invoice_type,
        invoiceDate=issue_date,
        sellerNTNCNIC=national_tax_number,
        sellerBusinessName=seller_business_name,
        sellerProvince=seller_province,
        sellerAddress=seller_address,
        buyerNTNCNIC=customer_national_tax_number,
        buyerBusinessName=customer.name,
        buyerProvince=customer_province,
        buyerAddress=customer_address,
        buyerRegistrationType=customer_registration_type,
        items=fbr_invoice_items,
    )

    if get_setting("DEBUG", default=False, raise_error=False):
        print(payload.model_dump_json(indent=2))

    return payload


# ---------------------------------------------------------------------------- #
#                           FBR Integration Functions                          #
# ---------------------------------------------------------------------------- #
def _get_base_payload(
    ntn: str,
    scenario_id: FBRIntegrationScenarioEnum = FBRIntegrationScenarioEnum.SN001,
) -> Dict[str, Any]:
    """Create base payload with dynamic NTN.

    Args:
        ntn: National Tax Number for the seller
        scenario_id: Scenario identifier to embed in the payload.

    Returns:
        Dict[str, Any]: Base payload dictionary
    """
    return {
        "invoiceType": "Sale Invoice",
        "invoiceDate": datetime.now().strftime("%Y-%m-%d"),
        "sellerNTNCNIC": ntn,
        "sellerBusinessName": "Test Seller Business Pvt Ltd",
        "sellerProvince": "Punjab",
        "sellerAddress": "123 Test Street, Lahore",
        "buyerNTNCNIC": "5205936",
        "buyerBusinessName": "TeamMates LLC",
        "buyerProvince": "Sindh",
        "buyerAddress": "456 Test Avenue, Karachi",
        "buyerRegistrationType": "Registered",
        "invoiceRefNo": "INV-001",
        "scenarioId": scenario_id.value,
        "items": [
            {
                "hsCode": "0101.2100",
                "productDescription": "Sample Product for FBR Test",
                "rate": "18%",
                "uoM": "Numbers, pieces, units",
                "quantity": 1,
                "totalValues": 118.0,
                "valueSalesExcludingST": 100.0,
                "fixedNotifiedValueOrRetailPrice": 118.0,
                "salesTaxApplicable": 18.0,
                "salesTaxWithheldAtSource": 18.0,
                "extraTax": 0.0,
                "furtherTax": 0.0,
                "fedPayable": 0.0,
                "discount": 0.0,
                "sroScheduleNo": "",
                "saleType": "Goods at standard rate (default)",
                "sroItemSerialNo": "",
            }
        ],
    }


def _extract_scenario_id(
    scenario: ScenarioDefinition,
) -> FBRIntegrationScenarioEnum:
    """Get the typed scenario identifier from a scenario definition."""

    if not scenario.payloadOverrides or not scenario.payloadOverrides.get("scenarioId"):
        raise InternalServerErrorException(
            message="Invalid FBR scenario definition",
            detail="Scenario definition is missing the scenarioId payload override.",
            extra={"scenario_name": scenario.name},
        )

    scenario_id = scenario.payloadOverrides["scenarioId"]

    try:
        return FBRIntegrationScenarioEnum(str(scenario_id))
    except ValueError as exc:
        raise InternalServerErrorException(
            message="Unsupported FBR scenario definition",
            detail=f"Scenario ID '{scenario_id}' is not part of the allowed integration scenarios.",
            extra={"scenario_name": scenario.name, "scenario_id": str(scenario_id)},
        ) from exc


def _get_scenario_definitions(
    scenarios: Optional[List[FBRIntegrationScenarioEnum]] = None,
) -> List[ScenarioDefinition]:
    """Get all scenario definitions.

    Returns:
        List[ScenarioDefinition]: List of all 27 test scenarios
    """
    definitions = [
        ScenarioDefinition(
            name="SN001: Goods at standard rate to registered buyers",
            payloadOverrides={"scenarioId": "SN001"},
            itemProperties={"saleType": "Goods at standard rate (default)"},
        ),
        ScenarioDefinition(
            name="SN002: Goods at standard rate to unregistered buyers",
            payloadOverrides={
                "scenarioId": "SN002",
                "buyerNTNCNIC": "1111111",
                "buyerRegistrationType": "Unregistered",
            },
            itemProperties={"saleType": "Goods at standard rate (default)"},
        ),
        ScenarioDefinition(
            name="SN003: Sale of Steel (Melted and Re-Rolled)",
            payloadOverrides={"scenarioId": "SN003"},
            itemProperties={
                "hsCode": "7206.1000",
                "uoM": "MT",
                "totalValues": 194624.48,
                "valueSalesExcludingST": 164936.0,
                "fixedNotifiedValueOrRetailPrice": 164936.0,
                "salesTaxApplicable": 29688.48,
                "salesTaxWithheldAtSource": 29688.48,
                "saleType": "Steel melting and re-rolling",
            },
        ),
        ScenarioDefinition(
            name="SN004: Sale by Ship Breakers",
            payloadOverrides={"scenarioId": "SN004"},
            itemProperties={
                "hsCode": "7204.4910",
                "uoM": "MT",
                "totalValues": 182459.86,
                "valueSalesExcludingST": 154627.0,
                "fixedNotifiedValueOrRetailPrice": 154627.0,
                "salesTaxApplicable": 27832.86,
                "salesTaxWithheldAtSource": 27832.86,
                "saleType": "Ship breaking",
            },
        ),
        ScenarioDefinition(
            name="SN005: Reduced rate sale",
            payloadOverrides={"scenarioId": "SN005"},
            itemProperties={
                "extraTax": "",
                "sroScheduleNo": "EIGHTH SCHEDULE Table 1",
                "saleType": "Goods at Reduced Rate",
                "sroItemSerialNo": "47",
            },
        ),
        ScenarioDefinition(
            name="SN006: Exempt goods sale",
            payloadOverrides={"scenarioId": "SN006"},
            itemProperties={
                "rate": "Exempt",
                "totalValues": 100.0,
                "valueSalesExcludingST": 100.0,
                "fixedNotifiedValueOrRetailPrice": 100.0,
                "salesTaxApplicable": 0.0,
                "salesTaxWithheldAtSource": 0.0,
                "sroScheduleNo": "6th Schd Table I",
                "saleType": "Exempt goods",
                "sroItemSerialNo": "166",
            },
        ),
        ScenarioDefinition(
            name="SN007: Zero rated sale",
            payloadOverrides={"scenarioId": "SN007"},
            itemProperties={
                "rate": "0%",
                "totalValues": 100.0,
                "fixedNotifiedValueOrRetailPrice": 100.0,
                "salesTaxApplicable": 0.0,
                "salesTaxWithheldAtSource": 0.0,
                "sroScheduleNo": "327(I)/2008",
                "saleType": "Goods at zero-rate",
                "sroItemSerialNo": "1",
            },
        ),
        ScenarioDefinition(
            name="SN008: Sale of 3rd schedule goods",
            payloadOverrides={"scenarioId": "SN008"},
            itemProperties={
                "fixedNotifiedValueOrRetailPrice": 100.0,
                "saleType": "3rd Schedule Goods",
            },
        ),
        ScenarioDefinition(
            name="SN009: Cotton Spinners purchase from Cotton Ginners (Textile Sector)",
            payloadOverrides={"scenarioId": "SN009"},
            itemProperties={"saleType": "Cotton ginners"},
        ),
        ScenarioDefinition(
            name="SN010: Mobile Operators adds Sale (Telecom Sector)",
            payloadOverrides={"scenarioId": "SN010"},
            itemProperties={
                "rate": "18.5%",
                "totalValues": 118.5,
                "fixedNotifiedValueOrRetailPrice": 118.5,
                "salesTaxApplicable": 18.5,
                "salesTaxWithheldAtSource": 18.5,
                "saleType": "Telecommunication services",
            },
        ),
        ScenarioDefinition(
            name="SN011: Toll Manufacturing sale by Steel sector",
            payloadOverrides={"scenarioId": "SN011"},
            itemProperties={
                "hsCode": "7214.9990",
                "uoM": "MT",
                "totalValues": 205000.0,
                "valueSalesExcludingST": 205000.0,
                "fixedNotifiedValueOrRetailPrice": 205000.0,
                "salesTaxApplicable": 36900.0,
                "salesTaxWithheldAtSource": 36900.0,
                "saleType": "Toll Manufacturing",
            },
        ),
        ScenarioDefinition(
            name="SN012: Sale of Petroleum products",
            payloadOverrides={"scenarioId": "SN012"},
            itemProperties={"saleType": "Petroleum Products"},
        ),
        ScenarioDefinition(
            name="SN013: Electricity Supply to Retailers",
            payloadOverrides={"scenarioId": "SN013"},
            itemProperties={
                "rate": "7.5%",
                "totalValues": 117.5,
                "fixedNotifiedValueOrRetailPrice": 17.5,
                "salesTaxApplicable": 7.5,
                "salesTaxWithheldAtSource": 7.5,
                "saleType": "Electricity Supply to Retailers",
            },
        ),
        ScenarioDefinition(
            name="SN014: Sale of Gas to CNG stations",
            payloadOverrides={"scenarioId": "SN014"},
            itemProperties={"saleType": "Gas to CNG stations"},
        ),
        ScenarioDefinition(
            name="SN015: Sale of mobile phones",
            payloadOverrides={"scenarioId": "SN015"},
            itemProperties={
                "sroScheduleNo": "NINTH SCHEDULE",
                "saleType": "Mobile Phones",
                "sroItemSerialNo": "1(A)",
            },
        ),
        ScenarioDefinition(
            name="SN016: Processing/Conversion of Goods",
            payloadOverrides={"scenarioId": "SN016"},
            itemProperties={"saleType": "Processing/Conversion of Goods"},
        ),
        ScenarioDefinition(
            name="SN017: Sale of Goods where FED is charged in ST mode",
            payloadOverrides={"scenarioId": "SN017"},
            itemProperties={
                "rate": "17%",
                "totalValues": 117.0,
                "fixedNotifiedValueOrRetailPrice": 117.0,
                "salesTaxApplicable": 17.0,
                "salesTaxWithheldAtSource": 17.0,
                "saleType": "Goods (FED in ST Mode)",
            },
        ),
        ScenarioDefinition(
            name="SN018: Sale of Services where FED is charged in ST mode",
            payloadOverrides={
                "invoiceType": "Sale Invoice",
                "scenarioId": "SN018",
            },
            itemProperties={
                "rate": "17%",
                "totalValues": 117.0,
                "fixedNotifiedValueOrRetailPrice": 117.0,
                "salesTaxApplicable": 17.0,
                "salesTaxWithheldAtSource": 17.0,
                "saleType": "Services (FED in ST Mode)",
            },
        ),
        ScenarioDefinition(
            name="SN019: Sale of Services",
            payloadOverrides={"scenarioId": "SN019"},
            itemProperties={
                "rate": "18.5%",
                "totalValues": 118.5,
                "fixedNotifiedValueOrRetailPrice": 118.5,
                "salesTaxApplicable": 18.5,
                "salesTaxWithheldAtSource": 18.5,
                "saleType": "Services",
            },
        ),
        ScenarioDefinition(
            name="SN020: Sale of Electric Vehicles",
            payloadOverrides={"scenarioId": "SN020"},
            itemProperties={
                "rate": "1%",
                "totalValues": 101.0,
                "valueSalesExcludingST": 100.0,
                "fixedNotifiedValueOrRetailPrice": 101.0,
                "salesTaxApplicable": 1.0,
                "salesTaxWithheldAtSource": 1.0,
                "sroScheduleNo": "6th Schd Table III",
                "saleType": "Electric Vehicle",
                "sroItemSerialNo": "20",
            },
        ),
        ScenarioDefinition(
            name="SN021: Sale of Cement / Concrete Block",
            payloadOverrides={"scenarioId": "SN021"},
            itemProperties={
                "rate": "Rs.10",
                "totalValues": 110.0,
                "fixedNotifiedValueOrRetailPrice": 110.0,
                "salesTaxApplicable": 10.0,
                "salesTaxWithheldAtSource": 10.0,
                "saleType": "Cement /Concrete Block",
            },
        ),
        ScenarioDefinition(
            name="SN022: Sale of Potassium Chlorate",
            payloadOverrides={"scenarioId": "SN022"},
            itemProperties={
                "hsCode": "2829.1910",
                "rate": "18% along with rupees 60 per kilogram",
                "uoM": "KG",
                "totalValues": 178.0,
                "valueSalesExcludingST": 100.0,
                "fixedNotifiedValueOrRetailPrice": 178.0,
                "salesTaxApplicable": 78.0,
                "salesTaxWithheldAtSource": 78.0,
                "sroScheduleNo": "EIGHTH SCHEDULE Table 1",
                "saleType": "Potassium Chlorate",
                "sroItemSerialNo": "56",
            },
        ),
        ScenarioDefinition(
            name="SN023: Sale of CNG Sales",
            payloadOverrides={"scenarioId": "SN023"},
            itemProperties={
                "rate": "Rs.200",
                "totalValues": 300.0,
                "fixedNotifiedValueOrRetailPrice": 300.0,
                "salesTaxApplicable": 200.0,
                "salesTaxWithheldAtSource": 200.0,
                "sroScheduleNo": "581(1)/2024",
                "saleType": "CNG Sales",
                "sroItemSerialNo": "Region-I",
            },
        ),
        ScenarioDefinition(
            name="SN024: Goods sold that are listed in SRO 297(I)/2023",
            payloadOverrides={"scenarioId": "SN024"},
            itemProperties={
                "rate": "25%",
                "totalValues": 125.0,
                "fixedNotifiedValueOrRetailPrice": 125.0,
                "salesTaxApplicable": 25.0,
                "salesTaxWithheldAtSource": 25.0,
                "sroScheduleNo": "297(I)/2023-Table-I",
                "saleType": "Goods as per SRO.297(|)/2023",
                "sroItemSerialNo": "12",
            },
        ),
        ScenarioDefinition(
            name="SN025: Drugs sold at fixed ST rate under serial 81 of Eighth Schedule Table I",
            payloadOverrides={"scenarioId": "SN025"},
            itemProperties={
                "rate": "0%",
                "totalValues": 100.0,
                "fixedNotifiedValueOrRetailPrice": 100.0,
                "salesTaxApplicable": 0.0,
                "salesTaxWithheldAtSource": 0.0,
                "sroScheduleNo": "Eighth Schedule Table 1",
                "saleType": "Non-Adjustable Supplies",
                "sroItemSerialNo": "81",
            },
        ),
        ScenarioDefinition(
            name="SN026: Sale to End Consumer by retailers",
            payloadOverrides={"scenarioId": "SN026"},
            itemProperties={"saleType": "Goods at standard rate (default)"},
        ),
        ScenarioDefinition(
            name="SN027: Sale to End Consumer by retailers",
            payloadOverrides={"scenarioId": "SN027"},
            itemProperties={
                "rate": "18%",
                "totalValues": 118.0,
                "fixedNotifiedValueOrRetailPrice": 100.0,
                "salesTaxApplicable": 18.0,
                "salesTaxWithheldAtSource": 18.0,
                "saleType": "3rd Schedule Goods",
            },
        ),
        ScenarioDefinition(
            name="SN028: Sale to End Consumer by retailers",
            payloadOverrides={"scenarioId": "SN028"},
            itemProperties={
                "extraTax": "",
                "sroScheduleNo": "EIGHTH SCHEDULE Table 1",
                "saleType": "Goods at Reduced Rate",
                "sroItemSerialNo": "47",
            },
        ),
    ]

    if scenarios is None or len(scenarios) == 0:
        return definitions

    allowed_scenarios = set(scenarios)
    return [
        scenario
        for scenario in definitions
        if _extract_scenario_id(scenario) in allowed_scenarios
    ]


def generate_scenario_payloads(
    ntn: str,
    scenarios: Optional[List[FBRIntegrationScenarioEnum]] = None,
) -> List[ScenarioPayload]:
    """Generate scenario payloads with the provided NTN.

    Args:
        ntn: National Tax Number for the seller
        scenarios: Optional list of scenario identifiers to include.

    Returns:
        List[ScenarioPayload]: List of scenario objects with metadata and payloads
    """
    scenario_definitions = _get_scenario_definitions(scenarios=scenarios)
    scenario_payloads = []

    for scenario in scenario_definitions:
        scenario_id = _extract_scenario_id(scenario)

        # Deep copy the base payload to ensure clean slate
        current_payload = deepcopy(_get_base_payload(ntn, scenario_id=scenario_id))

        # Apply top-level payload overrides if provided
        if scenario.payloadOverrides:
            current_payload.update(scenario.payloadOverrides)

        # Apply item-level overrides if provided
        if scenario.itemProperties:
            current_payload["items"][0].update(scenario.itemProperties)

        scenario_payloads.append(
            ScenarioPayload(
                scenario_id=scenario_id.value,
                name=scenario.name,
                payload=current_payload,
            )
        )

    return scenario_payloads


# ---------------------------------------------------------------------------- #
#                               FBR UOM FUNCTION                               #
# ------------------ Defined here to avoid circular imports ------------------ #
# ---------------------------------------------------------------------------- #
async def get_fbr_uom(
    auth_user: AuthUser, input_params: FBRUOMRequest
) -> FBRUOMResponse:
    """Retrieve the unit of measurement description for a given HS code.

    Args:
        auth_user: Authenticated user context including database session.
        input_params: Request parameters containing the HS code and annexure ID.

    Returns:
        FBRUOMResponse: Response payload containing the unit of measurement description.

    Raises:
        BadRequestException: If the sandbox token is missing or the FBR API returns an error.
    """

    annexure_id = input_params.annexure_id or "1"
    query_params = {
        "hs_code": input_params.hs_code,
        "annexure_id": annexure_id,
    }

    http_response = await get_fbr_request(
        url=get_setting("FBR_API_HS_UOM_URL"),
        token=get_setting("FBR_API_ADMIN_PRODUCTION_TOKEN"),
        query_params=query_params,
    )

    # Check HTTP status code
    if http_response.status_code != 200:
        raise BadRequestException(
            message="FBR UOM request failed",
            detail=f"FBR API returned status code {http_response.status_code}",
            extra={
                "operation": "fbr_get_uom",
                "user_id": str(auth_user.user.id),
                "hs_code": input_params.hs_code,
                "annexure_id": annexure_id,
                "status_code": http_response.status_code,
            },
        )

    # Parse response body
    try:
        data = http_response.json()
    except ValueError as exc:
        raise BadRequestException(
            message="Failed to parse FBR UOM response",
            detail="The response body is not valid JSON",
            extra={
                "operation": "fbr_get_uom",
                "hs_code": input_params.hs_code,
            },
        ) from exc

    # Extract UOM descriptions
    units_of_measurement: List[str] = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                description = item.get("description", None)
                if description:
                    units_of_measurement.append(str(description))

    return FBRUOMResponse(units_of_measurement=units_of_measurement)
