# src\fbr\schemas.py
"""Schema definitions for the FBR module."""

# src\fbr\schemas.py

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.fbr.enums import FBRIntegrationScenarioEnum
from src.schemas import OptionalUserIDMixin


# ---------------------------------- FBR API --------------------------------- #
class FBRItemError(SQLModel):
    """
    Represents an error for a single invoice item.

    Attributes:
        item_no (str): Item serial number in the invoice
        error (str): Error message for this item
    """

    item_no: str = Field(description="Item serial number in the invoice")
    error: str = Field(description="Error message for this item")


class FBRParsedResponse(SQLModel):
    """
    Normalized representation of an FBR API response.

    Attributes:
        success (bool): Indicates if the overall validation succeeded.
        status (str): HTTP status code (e.g., "HTTP_200", "HTTP_400").
        message (str): Human-readable summary of the response.
        error (Optional[str]): Top-level error message, if any.
        item_errors (List[FBRItemError]): List of errors for individual items.
        reference (Optional[str]): Overall reference number, if provided.
        response_body (Optional[Dict[str, Any]]): Complete raw response for debugging.
    """

    success: bool = Field(description="Indicates if the overall validation succeeded.")
    status: str = Field(description="HTTP status code (e.g., HTTP_200, HTTP_400).")
    message: str = Field(description="Human-readable summary of the response.")
    error: Optional[str] = Field(default=None, description="Top-level error message.")
    item_errors: List[FBRItemError] = Field(
        default_factory=list, description="List of errors for individual items."
    )
    reference: Optional[str] = Field(
        default=None, description="Overall reference number assigned by FBR."
    )
    response_body: Optional[Dict[str, Any]] = Field(
        default=None, description="Complete raw response for debugging."
    )


class FBRInvoiceActionRequest(SQLModel):
    """
    Request model for performing FBR invoice actions.

    Attributes:
        invoice_id (UUID): Unique identifier of the invoice to process with the FBR.
    """

    invoice_id: UUID = Field(
        nullable=False,
        description="Unique identifier of the invoice to process with the FBR.",
    )

    sandbox_mode: bool = Field(
        default=False,
        description="Flag indicating whether to use sandbox mode for the FBR API.",
    )


class FBRValidationRequest(FBRInvoiceActionRequest):
    """
    Request model for validating an invoice with the FBR.

    Attributes:
        invoice_id (UUID): Unique identifier of the invoice to validate with the FBR.
    """

    pass


class FBRValidationResponse(FBRParsedResponse):
    """
    Response model for FBR invoice validation.

    Attributes:
        success (bool): Indicates if the overall validation succeeded.
        status (str): HTTP status code (e.g., "HTTP_200", "HTTP_400").
        message (str): Human-readable summary of the response.
        error (Optional[str]): Top-level error message, if any.
        item_errors (List[FBRItemError]): List of errors for individual items.
        reference (Optional[str]): Overall reference number, if provided.
        response_body (Optional[Dict[str, Any]]): Complete raw response for debugging.
    """

    pass


class FBRSubmissionRequest(FBRInvoiceActionRequest):
    """
    Request model for submitting an invoice to the FBR.

    Attributes:
        invoice_id (UUID): Unique identifier of the invoice to submit to the FBR.
    """

    pass


class FBRSubmissionResponse(FBRParsedResponse):
    """
    Response model for FBR invoice submission.

    Attributes:
        success (bool): Indicates if the overall submission succeeded.
        status (str): HTTP status code (e.g., "HTTP_200", "HTTP_400").
        message (str): Human-readable summary of the response.
        error (Optional[str]): Top-level error message, if any.
        item_errors (List[FBRItemError]): List of errors for individual items.
        reference (Optional[str]): Overall reference number, if provided.
        response_body (Optional[Dict[str, Any]]): Complete raw response for debugging.
    """

    pass


class FBRIntegrationScenarioResultBase(SQLModel):
    """
    Base structure describing the outcome of an FBR integration scenario.

    Attributes:
        scenario_id (str): Identifier provided by the FBR for the test scenario.
        name (str): Human-readable scenario name.
        status (str): Status returned by the FBR for the scenario.
        success (bool): Indicates if the scenario completed successfully.
        message (str): Additional information or error details for the scenario.
        response_body (Optional[Dict[str, Any]]): Raw response body returned by the FBR for the scenario.
    """

    scenario_id: str = Field(
        nullable=False,
        description="Identifier provided by the FBR for the test scenario.",
    )
    name: str = Field(
        nullable=False,
        description="Human-readable scenario name.",
    )
    status: str = Field(
        nullable=False,
        description="Status returned by the FBR for the scenario.",
    )
    success: bool = Field(
        default=False,
        nullable=False,
        description="Indicates if the scenario completed successfully.",
    )
    message: str = Field(
        nullable=False,
        description="Additional information or error details for the scenario.",
    )
    response_body: Dict[str, Any] = Field(
        default={},
        description="Raw response body returned by the FBR for the scenario.",
    )


class FBRIntegrationScenarioResultResponse(FBRIntegrationScenarioResultBase):
    """
    Response model describing an executed FBR integration scenario.

    Attributes:
        scenario_id (str): Identifier provided by the FBR for the test scenario.
        name (str): Human-readable scenario name.
        status (str): Status returned by the FBR for the scenario.
        success (bool): Indicates if the scenario completed successfully.
        message (str): Additional information or error details for the scenario.
        response_body (Dict[str, Any]): Raw response body returned by the FBR for the scenario.
    """

    pass


class FBRIntegrationResponse(SQLModel):
    """
    Response model for executing the FBR integration validation suite.

    Attributes:
        success (bool): Indicates if at least one scenario succeeded.
        message (str): Summary message about the integration outcome.
        scenarios (list[FBRIntegrationScenarioResultResponse]): Details for each scenario executed.
    """

    success: bool = Field(
        nullable=False,
        description="Indicates if at least one scenario succeeded.",
    )
    message: str = Field(
        nullable=False,
        description="Summary message about the integration outcome.",
    )
    scenarios: List[FBRIntegrationScenarioResultResponse] = Field(
        default_factory=list,
        description="Details for each scenario executed.",
    )


class FBRIntegrationRequest(OptionalUserIDMixin):
    """
    Request model for executing FBR integration scenarios.

    Attributes:
        user_id (Optional[UUID]): Unique identifier for the user.
        scenarios (Optional[List[FBRIntegrationScenarioEnum]]): Scenario identifiers to execute. If omitted, all supported scenarios are run.
    """

    scenarios: Optional[List[FBRIntegrationScenarioEnum]] = Field(
        default=None,
        description="Scenario identifiers to execute. If omitted, all supported scenarios are run.",
    )


class FBRUOMRequest(SQLModel):
    """
    Request model for fetching FBR Unit of Measurement (UOM) codes.

    Attributes:
        hs_code (str): HS Code to filter UOM codes.
        annexure_id (str): Annexure ID to filter UOM codes.
    """

    hs_code: str = Field(
        description="HS Code to filter UOM codes.",
    )
    annexure_id: str = Field(
        description="Annexure ID to filter UOM codes.",
    )


class FBRUOMResponse(SQLModel):
    """
    Response model for FBR Unit of Measurement (UOM) codes.

    Attributes:
        units_of_measurement (Optional[List[str]]): Units of Measurement.
    """

    units_of_measurement: Optional[List[str]] = Field(
        default=None,
        description="Units of Measurement.",
    )


class FBRInvoiceItem(SQLModel):
    """
    Single line item in an FBR invoice.

    Attributes:
        hsCode (str): Harmonized System Code for the product.
        productDescription (str): Description of the product.
        rate (str): Tax rate applicable to the product.
        uoM (str): Unit of Measure for the product.
        quantity (float): Quantity of the product.
        totalValues (float): Total values for the product.
        valueSalesExcludingST (float): Sales value excluding sales tax.
        fixedNotifiedValueOrRetailPrice (float): Fixed notified value or retail price.
        salesTaxApplicable (float): Sales tax applicable to the product.
        salesTaxWithheldAtSource (float): Sales tax withheld at source.
        extraTax (float): Any extra tax applicable.
        furtherTax (float): Any further tax applicable.
        fedPayable (float): Federal tax payable.
        discount (float): Any discount applicable.
        sroScheduleNo (str): SRO Schedule Number.
        saleType (str): Type of sale.
        sroItemSerialNo (str): SRO Item Serial Number.
    """

    hsCode: str = Field(description="Harmonized System Code for the product.")
    productDescription: str = Field(description="Description of the product.")
    rate: str = Field(description="Tax rate applicable to the product.")
    uoM: str = Field(description="Unit of Measure for the product.")
    quantity: float = Field(description="Quantity of the product.")
    totalValues: float = Field(description="Total values for the product.")
    valueSalesExcludingST: float = Field(description="Sales value excluding sales tax.")
    fixedNotifiedValueOrRetailPrice: float = Field(
        description="Fixed notified value or retail price."
    )
    salesTaxApplicable: float = Field(
        description="Sales tax applicable to the product."
    )
    salesTaxWithheldAtSource: float = Field(description="Sales tax withheld at source.")
    extraTax: float = Field(description="Any extra tax applicable.")
    furtherTax: float = Field(description="Any further tax applicable.")
    fedPayable: float = Field(description="Federal tax payable.")
    discount: float = Field(description="Any discount applicable.")
    sroScheduleNo: str = Field(description="SRO Schedule Number.")
    saleType: str = Field(description="Type of sale.")
    sroItemSerialNo: str = Field(description="SRO Item Serial Number.")


class FBRInvoice(SQLModel):
    """
    Complete FBR invoice payload structure.

    Attributes:
        invoiceType (str): Type of the invoice.
        invoiceDate (str): Date of the invoice in YYYY-MM-DD format.
        sellerNTNCNIC (str): Seller's National Tax Number or CNIC.
        sellerBusinessName (str): Name of the seller's business.
        sellerProvince (str): Province of the seller.
        sellerAddress (str): Address of the seller.
        buyerNTNCNIC (str): Buyer's National Tax Number or CNIC.
        buyerBusinessName (str): Name of the buyer's business.
        buyerProvince (str): Province of the buyer.
        buyerAddress (str): Address of the buyer.
        buyerRegistrationType (str): Registration type of the buyer.
        invoiceRefNo (str): Reference number for the invoice.
        items (List[Dict[str, Any]]): List of line items in the invoice.
    """

    invoiceType: str = Field(description="Type of the invoice.")
    invoiceDate: str = Field(description="Date of the invoice in YYYY-MM-DD format.")
    sellerNTNCNIC: str = Field(description="Seller's National Tax Number or CNIC.")
    sellerBusinessName: str = Field(description="Name of the seller's business.")
    sellerProvince: str = Field(description="Province of the seller.")
    sellerAddress: str = Field(description="Address of the seller.")
    buyerNTNCNIC: str = Field(description="Buyer's National Tax Number or CNIC.")
    buyerBusinessName: str = Field(description="Name of the buyer's business.")
    buyerProvince: str = Field(description="Province of the buyer.")
    buyerAddress: str = Field(description="Address of the buyer.")
    buyerRegistrationType: str = Field(description="Registration type of the buyer.")
    invoiceRefNo: str = Field(description="Reference number for the invoice.")
    sourceInvoiceNo: str = Field(
        default=None, description="Source invoice number, if applicable."
    )
    items: List[FBRInvoiceItem] = Field(
        description="List of line items in the invoice."
    )


class FBRInvoiceSandbox(FBRInvoice):
    """
    FBR invoice payload structure for sandbox/testing environment.

    Attributes:
        invoiceType (str): Type of the invoice.
        invoiceDate (str): Date of the invoice in YYYY-MM-DD format.
        sellerNTNCNIC (str): Seller's National Tax Number or CNIC.
        sellerBusinessName (str): Name of the seller's business.
        sellerProvince (str): Province of the seller.
        sellerAddress (str): Address of the seller.
        buyerNTNCNIC (str): Buyer's National Tax Number or CNIC.
        buyerBusinessName (str): Name of the buyer's business.
        buyerProvince (str): Province of the buyer.
        buyerAddress (str): Address of the buyer.
        buyerRegistrationType (str): Registration type of the buyer.
        invoiceRefNo (str): Reference number for the invoice.
        items (List[Dict[str, Any]]): List of line items in the invoice.
        scenarioId (str): Identifier for the sandbox scenario.
    """

    scenarioId: str = Field(
        description="Identifier for the sandbox scenario.",
    )


class ScenarioDefinition(SQLModel):
    """
    Definition for a single test scenario.
    Attributes:
        name (str): Name of the test scenario.
        payloadOverrides (Optional[Dict[str, Any]]): Overrides for the scenario payload.
        itemProperties (Optional[Dict[str, Any]]): Properties for the items in the scenario.
    """

    name: str = Field(description="Name of the test scenario.")
    payloadOverrides: Optional[Dict[str, Any]] = Field(
        default=None, description="Overrides for the scenario payload."
    )
    itemProperties: Optional[Dict[str, Any]] = Field(
        default=None, description="Properties for the items in the scenario."
    )


class ScenarioPayload(SQLModel):
    """
    Container for scenario metadata and its generated payload.

    Attributes:
        scenario_id (str): Unique identifier for the scenario.
        name (str): Name of the scenario.
        payload (Dict[str, Any]): Generated payload for the scenario.
    """

    scenario_id: str = Field(description="Unique identifier for the scenario.")
    name: str = Field(description="Name of the scenario.")
    payload: Dict[str, Any] = Field(description="Generated payload for the scenario.")
