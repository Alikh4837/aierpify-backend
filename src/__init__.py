# src\__init__.py
"""
Main application package initialization.
Configures global settings including warning filters.
"""

import warnings

# Suppress Pydantic enum serialization warnings
warnings.filterwarnings(
    "ignore",
    message=".*Pydantic serializer warnings.*",
    category=UserWarning,
    module="pydantic.main",
)
