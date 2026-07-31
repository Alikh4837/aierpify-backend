# src\stats\schemas.py
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------- #
#                                 Base Schemas                                 #
# ---------------------------------------------------------------------------- #
class ProductWeeklyStats(BaseModel):
    """Weekly statistics for products."""

    week_start: datetime = Field(description="Start date of the week")
    products_created: int = Field(description="Number of products created this week")

    class Config:
        json_schema_extra = {
            "example": {"week_start": "2025-01-06T00:00:00Z", "products_created": 12}
        }


class InvoiceWeeklyStats(BaseModel):
    """Weekly statistics for invoices and sales."""

    week_start: datetime = Field(description="Start date of the week")
    invoices_created: int = Field(description="Number of invoices created this week")
    total_revenue: float = Field(description="Total revenue generated this week")
    total_tax_collected: float = Field(description="Total tax amount collected")
    avg_invoice_value: float = Field(description="Average invoice value")
    max_invoice_value: float = Field(description="Highest invoice value")
    min_invoice_value: float = Field(description="Lowest invoice value")
    units_sold: int = Field(description="Total units/products sold this week")
    unique_products_sold: int = Field(description="Number of unique products sold")
    avg_discount: float = Field(description="Average discount percentage applied")

    class Config:
        json_schema_extra = {
            "example": {
                "week_start": "2025-01-06T00:00:00Z",
                "invoices_created": 45,
                "total_revenue": 125000.50,
                "total_tax_collected": 22500.09,
                "avg_invoice_value": 2777.78,
                "max_invoice_value": 15000.00,
                "min_invoice_value": 500.00,
                "units_sold": 320,
                "unique_products_sold": 28,
                "avg_discount": 5.2,
            }
        }


class CustomerWeeklyStats(BaseModel):
    """Weekly statistics for customers."""

    week_start: datetime = Field(description="Start date of the week")
    customers_created: int = Field(description="Number of new customers this week")
    active_customers: int = Field(description="Number of customers who made purchases")
    avg_invoices_per_customer: float = Field(
        description="Average invoices per active customer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "week_start": "2025-01-06T00:00:00Z",
                "customers_created": 8,
                "active_customers": 35,
                "avg_invoices_per_customer": 1.29,
            }
        }


class QuarterlyStats(BaseModel):
    """Aggregated statistics for a complete quarter."""

    quarter: int = Field(description="Quarter number (1-4)")
    year: int = Field(description="Year")
    start_date: datetime = Field(description="Quarter start date")
    end_date: datetime = Field(description="Quarter end date")

    # Invoice statistics
    total_invoices: int = Field(description="Total invoices in quarter")
    total_revenue: float = Field(description="Total revenue for quarter")
    total_tax_collected: float = Field(description="Total tax collected")
    avg_invoice_value: float = Field(description="Average invoice value")

    # Product statistics
    total_units_sold: int = Field(description="Total units sold")
    unique_products_sold: int = Field(description="Unique products sold")
    products_created: int = Field(description="New products created")

    # Customer statistics
    new_customers: int = Field(description="New customers acquired")
    active_customers: int = Field(description="Customers who made purchases")

    # Weekly breakdowns
    weekly_invoices: List[InvoiceWeeklyStats] = Field(
        description="Week-by-week invoice stats"
    )
    weekly_products: List[ProductWeeklyStats] = Field(
        description="Week-by-week product stats"
    )
    weekly_customers: List[CustomerWeeklyStats] = Field(
        description="Week-by-week customer stats"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quarter": 1,
                "year": 2025,
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-03-31T23:59:59Z",
                "total_invoices": 450,
                "total_revenue": 1250000.00,
                "total_tax_collected": 225000.00,
                "avg_invoice_value": 2777.78,
                "total_units_sold": 3200,
                "unique_products_sold": 85,
                "products_created": 25,
                "new_customers": 78,
                "active_customers": 320,
                "weekly_invoices": [],
                "weekly_products": [],
                "weekly_customers": [],
            }
        }


class EmptyQuarterResponse(BaseModel):
    """Response for quarters that haven't started yet."""

    quarter: int
    year: int
    message: str = Field(description="Explanation why no data is available")

    class Config:
        json_schema_extra = {
            "example": {
                "quarter": 4,
                "year": 2025,
                "message": "Quarter 4 of 2025 has not started yet",
            }
        }


class InvoiceStatsResponse(BaseModel):
    """Complete response containing all requested quarterly statistics."""

    year: int = Field(description="Year for which stats were generated")
    current_quarter: int = Field(description="Current quarter number")
    quarters: List[QuarterlyStats] = Field(
        description="Statistics for each requested quarter"
    )
    empty_quarters: List[EmptyQuarterResponse] = Field(
        default=[], description="Quarters that haven't started yet"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2025,
                "current_quarter": 1,
                "quarters": [],
                "empty_quarters": [],
            }
        }


# ---------------------------------------------------------------------------- #
#                               Endpoint Schemas                               #
# ---------------------------------------------------------------------------- #
class GetInvoiceStatsRequest(BaseModel):
    """Request schema for fetching statistics."""

    year: int = Field(description="Year for which to fetch statistics", ge=1970)
    quarters: Optional[List[Literal[1, 2, 3, 4]]] = Field(
        default=None,
        max_length=4,
        description="List of quarters (1-4) to include in the statistics",
    )


class GetInvoiceStatsResponse(InvoiceStatsResponse):
    """Response schema for statistics request."""

    pass
