# src\stats\service.py
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select

from src.auth.user import AuthUser
from src.customers.models import Customer
from src.invoices.models import Invoice, InvoiceItem
from src.products.models import Product
from src.stats.schemas import (
    CustomerWeeklyStats,
    EmptyQuarterResponse,
    GetInvoiceStatsRequest,
    InvoiceStatsResponse,
    InvoiceWeeklyStats,
    ProductWeeklyStats,
    QuarterlyStats,
)
from src.utils import get_user_id


class StatsService:
    """Service for generating statistics across quarters."""

    @staticmethod
    def get_quarter_dates(year: int, quarter: int) -> tuple[datetime, datetime]:
        """Get start and end dates for a given quarter."""
        quarter_starts = {
            1: (1, 1),
            2: (4, 1),
            3: (7, 1),
            4: (10, 1),
        }
        quarter_ends = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31),
        }

        start_month, start_day = quarter_starts[quarter]
        end_month, end_day = quarter_ends[quarter]

        start_date = datetime(
            year, start_month, start_day, 0, 0, 0, tzinfo=timezone.utc
        )
        end_date = datetime(year, end_month, end_day, 23, 59, 59, tzinfo=timezone.utc)

        return start_date, end_date

    @staticmethod
    def get_current_quarter(date: Optional[datetime] = None) -> tuple[int, int]:
        """Get current quarter and year."""
        if date is None:
            date = datetime.now(tz=timezone.utc)

        quarter = (date.month - 1) // 3 + 1
        return quarter, date.year

    @staticmethod
    async def get_weekly_invoice_stats(
        session, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[InvoiceWeeklyStats]:
        """Get weekly invoice statistics for a date range."""

        # Get invoice aggregates
        invoice_stmt = (
            select(
                func.date_trunc("week", Invoice.created_at).label("week_start"),
                func.count(col(Invoice.id)).label("invoices_created"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total_revenue"),
                func.coalesce(func.sum(Invoice.tax_amount), 0).label(
                    "total_tax_collected"
                ),
                func.coalesce(func.avg(Invoice.total_amount), 0).label(
                    "avg_invoice_value"
                ),
                func.coalesce(func.max(Invoice.total_amount), 0).label(
                    "max_invoice_value"
                ),
                func.coalesce(func.min(Invoice.total_amount), 0).label(
                    "min_invoice_value"
                ),
                func.coalesce(func.avg(Invoice.discount_amount), 0).label(
                    "avg_discount"
                ),
            )  # type: ignore
            .where(
                Invoice.user_id == user_id,
                Invoice.created_at >= start_date,
                Invoice.created_at <= end_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )

        invoice_results = (await session.exec(invoice_stmt)).all()

        # Get invoice item aggregates (units sold, unique products)
        items_stmt = (
            select(
                func.date_trunc("week", Invoice.created_at).label("week_start"),
                func.coalesce(func.sum(InvoiceItem.quantity), 0).label("units_sold"),
                func.count(func.distinct(InvoiceItem.product_id)).label(
                    "unique_products_sold"
                ),
            )
            .join(Invoice, col(InvoiceItem.invoice_id) == Invoice.id)
            .where(
                Invoice.user_id == user_id,
                Invoice.created_at >= start_date,
                Invoice.created_at <= end_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )

        items_results = (await session.exec(items_stmt)).all()

        # Merge results
        items_by_week = {row.week_start: row for row in items_results}

        stats = []
        for row in invoice_results:
            items_data = items_by_week.get(row.week_start)

            stats.append(
                InvoiceWeeklyStats(
                    week_start=row.week_start,
                    invoices_created=row.invoices_created,
                    total_revenue=float(row.total_revenue),
                    total_tax_collected=float(row.total_tax_collected),
                    avg_invoice_value=float(row.avg_invoice_value),
                    max_invoice_value=float(row.max_invoice_value),
                    min_invoice_value=float(row.min_invoice_value),
                    units_sold=int(items_data.units_sold) if items_data else 0,
                    unique_products_sold=int(items_data.unique_products_sold)
                    if items_data
                    else 0,
                    avg_discount=float(row.avg_discount),
                )
            )

        return stats

    @staticmethod
    async def get_weekly_product_stats(
        session, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[ProductWeeklyStats]:
        """Get weekly product statistics for a date range."""

        stmt = (
            select(
                func.date_trunc("week", Product.created_at).label("week_start"),
                func.count(col(Product.id)).label("products_created"),
            )
            .where(
                Product.user_id == user_id,
                Product.created_at >= start_date,
                Product.created_at <= end_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )

        results = (await session.exec(stmt)).all()

        return [
            ProductWeeklyStats(
                week_start=row.week_start,
                products_created=row.products_created,
            )
            for row in results
        ]

    @staticmethod
    async def get_weekly_customer_stats(
        session, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[CustomerWeeklyStats]:
        """Get weekly customer statistics for a date range."""

        # New customers per week
        customer_stmt = (
            select(
                func.date_trunc("week", Customer.created_at).label("week_start"),
                func.count(col(Customer.id)).label("customers_created"),
            )
            .where(
                Customer.user_id == user_id,
                Customer.created_at >= start_date,
                Customer.created_at <= end_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )

        customer_results = (await session.exec(customer_stmt)).all()

        # Active customers and invoices per customer per week
        active_stmt = (
            select(
                func.date_trunc("week", Invoice.created_at).label("week_start"),
                func.count(func.distinct(Invoice.customer_id)).label(
                    "active_customers"
                ),
                func.count(col(Invoice.id)).label("total_invoices"),
            )
            .where(
                Invoice.user_id == user_id,
                Invoice.created_at >= start_date,
                Invoice.created_at <= end_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )

        active_results = (await session.exec(active_stmt)).all()

        # Merge results
        active_by_week = {row.week_start: row for row in active_results}
        customer_by_week = {row.week_start: row for row in customer_results}

        # Get all unique weeks
        all_weeks = set(active_by_week.keys()) | set(customer_by_week.keys())

        stats = []
        for week in sorted(all_weeks):
            customer_data = customer_by_week.get(week)
            active_data = active_by_week.get(week)

            active_customers = active_data.active_customers if active_data else 0
            total_invoices = active_data.total_invoices if active_data else 0

            avg_invoices = (
                total_invoices / active_customers if active_customers else 0.0
            )

            stats.append(
                CustomerWeeklyStats(
                    week_start=week,
                    customers_created=customer_data.customers_created
                    if customer_data
                    else 0,
                    active_customers=active_customers,
                    avg_invoices_per_customer=round(avg_invoices, 2),
                )
            )

        return stats

    @staticmethod
    async def get_quarterly_stats(
        session, user_id: UUID, year: int, quarter: int
    ) -> QuarterlyStats:
        """Get complete statistics for a specific quarter."""

        start_date, end_date = StatsService.get_quarter_dates(year, quarter)

        # Get weekly breakdowns
        weekly_invoices = await StatsService.get_weekly_invoice_stats(
            session, user_id, start_date, end_date
        )
        weekly_products = await StatsService.get_weekly_product_stats(
            session, user_id, start_date, end_date
        )
        weekly_customers = await StatsService.get_weekly_customer_stats(
            session, user_id, start_date, end_date
        )

        # Calculate quarter totals
        total_invoices = sum(w.invoices_created for w in weekly_invoices)
        total_revenue = sum(w.total_revenue for w in weekly_invoices)
        total_tax_collected = sum(w.total_tax_collected for w in weekly_invoices)
        avg_invoice_value = (
            total_revenue / total_invoices if total_invoices > 0 else 0.0
        )

        total_units_sold = sum(w.units_sold for w in weekly_invoices)

        # Get unique products sold in the quarter (actual count)
        unique_products_stmt = (
            select(func.count(func.distinct(InvoiceItem.product_id)))
            .join(Invoice, col(InvoiceItem.invoice_id) == Invoice.id)
            .where(
                Invoice.user_id == user_id,
                Invoice.created_at >= start_date,
                Invoice.created_at <= end_date,
            )
        )

        unique_products_result = await session.exec(unique_products_stmt)
        unique_products_sold = unique_products_result.one() or 0

        products_created = sum(w.products_created for w in weekly_products)

        new_customers = sum(w.customers_created for w in weekly_customers)
        active_customers = max(
            (w.active_customers for w in weekly_customers), default=0
        )

        return QuarterlyStats(
            quarter=quarter,
            year=year,
            start_date=start_date,
            end_date=end_date,
            total_invoices=total_invoices,
            total_revenue=round(total_revenue, 2),
            total_tax_collected=round(total_tax_collected, 2),
            avg_invoice_value=round(avg_invoice_value, 2),
            total_units_sold=total_units_sold,
            unique_products_sold=int(unique_products_sold),
            products_created=products_created,
            new_customers=new_customers,
            active_customers=active_customers,
            weekly_invoices=weekly_invoices,
            weekly_products=weekly_products,
            weekly_customers=weekly_customers,
        )

    @staticmethod
    async def get_invoice_stats(
        auth_user: AuthUser,
        input_data: GetInvoiceStatsRequest,
    ) -> InvoiceStatsResponse:
        """
        Get invoice statistics for specified quarters.

        Args:
            session: Database session
            user_id: User ID to filter records
            year: Year for which to generate stats
            quarters: List of quarters (1-4) to generate stats for.
                     If None, generates stats for all quarters up to current quarter.

        Returns:
            InvoiceStatsResponse with quarterly statistics
        """

        session = auth_user.session
        user_id = get_user_id(auth_user)

        year = input_data.year
        quarters = input_data.quarters

        current_quarter, current_year = StatsService.get_current_quarter()

        # Determine which quarters to process
        if quarters is None:
            # Generate stats for all quarters up to current quarter
            if year < current_year:
                quarters = [1, 2, 3, 4]
            elif year == current_year:
                quarters = list(range(1, current_quarter + 1))
            else:
                # Future year
                quarters = []

        quarterly_stats = []
        empty_quarters = []

        for quarter in quarters:
            # Check if quarter has started
            quarter_start, _ = StatsService.get_quarter_dates(year, quarter)
            now = datetime.now(tz=timezone.utc)

            if quarter_start > now:
                empty_quarters.append(
                    EmptyQuarterResponse(
                        quarter=quarter,
                        year=year,
                        message=f"Quarter {quarter} of {year} has not started yet",
                    )
                )
            else:
                stats = await StatsService.get_quarterly_stats(
                    session, user_id, year, quarter
                )
                quarterly_stats.append(stats)

        return InvoiceStatsResponse(
            year=year,
            current_quarter=current_quarter if year == current_year else 0,
            quarters=quarterly_stats,
            empty_quarters=empty_quarters,
        )
