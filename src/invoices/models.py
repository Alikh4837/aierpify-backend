# src\invoices\models.py

from src.invoices.schemas import InvoiceBase, InvoiceItemBase
from src.models import DBIDMixin
from src.schemas import TimestampMixin


class Invoice(TimestampMixin, InvoiceBase, DBIDMixin, table=True):
    """
    An invoice document with tax calculations and FBR integration, extending the base schema with table configuration.
    Attributes are inherited from InvoiceBase.
    """

    pass


class InvoiceItem(TimestampMixin, InvoiceItemBase, DBIDMixin, table=True):
    """
    A line item within an invoice, extending the base schema with table configuration.
    Attributes are inherited from InvoiceItemBase.
    """

    pass
