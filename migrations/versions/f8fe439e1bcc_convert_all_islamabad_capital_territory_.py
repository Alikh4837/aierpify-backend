"""Convert all Islamabad Capital Territory Provinces to Capital Territory.

Revision ID: f8fe439e1bcc
Revises: 32b2a1a5620e
Create Date: 2025-12-15 14:33:11.576332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'f8fe439e1bcc'
down_revision: Union[str, Sequence[str], None] = '32b2a1a5620e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE customers
        SET province = 'Capital Territory'
        WHERE province = 'Islamabad Capital Territory';
    """)

    op.execute("""
        UPDATE user_profiles
        SET province = 'Capital Territory'
        WHERE province = 'Islamabad Capital Territory';
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE customers
        SET province = 'Islamabad Capital Territory'
        WHERE province = 'Capital Territory';
    """)

    op.execute("""
        UPDATE user_profiles
        SET province = 'Islamabad Capital Territory'
        WHERE province = 'Capital Territory';
    """)
