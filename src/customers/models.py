# src\customers\models.py
from src.customers.schemas import CustomerBase
from src.models import DBIDMixin
from src.schemas import TimestampMixin


class Customer(TimestampMixin, CustomerBase, DBIDMixin, table=True):
    """
    A customer profile associated with a user, stored in the database.
    Inherits all fields from CustomerBase.
    """

    pass
