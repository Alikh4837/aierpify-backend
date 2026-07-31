# migrations\versions\ded78d419128_add_features_to_subscription_plan.py
"""Add features to subscription plan

Revision ID: ded78d419128
Revises: 9b7d97c8a81f
Create Date: 2025-11-18 22:33:30.713637

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ded78d419128"
down_revision: Union[str, Sequence[str], None] = "9b7d97c8a81f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE subscription_plans
        ALTER COLUMN features
        TYPE TEXT[]
        USING CASE
            WHEN features IS NULL OR features = '' THEN '{}'
            ELSE string_to_array(features, ',')
        END;
        """
    )
    op.alter_column("subscription_plans", "features", nullable=True)

    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE subscription_plans
        ALTER COLUMN features
        TYPE VARCHAR
        USING array_to_string(features, ',');
        """
    )
    op.alter_column("subscription_plans", "features", nullable=False)
    # ### end Alembic commands ###
