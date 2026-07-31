# src\alembic.py

# This file is used to ensure that all models are imported
# when running Alembic migrations, so that the metadata is
# available for autogeneration of migration scripts.

from src.auth.models import *  # noqa: F403
from src.customers.models import *  # noqa: F403
from src.invoices.models import *  # noqa: F403
from src.products.models import *  # noqa: F403
from src.users.models import *  # noqa: F403
