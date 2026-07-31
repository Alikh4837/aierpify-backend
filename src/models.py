# src\models.py


from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class DBIDMixin(SQLModel):
    """
    Mixin for models with a database ID field.

    Attributes:
        id (UUID): Unique identifier for the record.
    """

    id: UUID = Field(
        primary_key=True,
        default_factory=uuid4,
        description="Unique identifier for the record.",
    )
