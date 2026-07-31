# src\products\models.py

from src.models import DBIDMixin
from src.products.schemas import HSCodeBase, ProductBase
from src.schemas import TimestampMixin


class Product(TimestampMixin, ProductBase, DBIDMixin, table=True):
    """
    A product or service that can be invoiced, stored in the database.
    Inherits all fields from ProductBase.
    """

    pass


class HSCode(TimestampMixin, HSCodeBase, DBIDMixin, table=True):
    """
    Harmonized System (HS) code for product classification, stored in the database.
    Inherits all fields from HSCodeBase.
    """

    pass
