# src\users\enums.py
from enum import StrEnum


class SubscriptionPlanPeriodEnum(StrEnum):
    """
    Enumeration of subscription plan billing periods.
    """

    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionPlanFeaturesEnum(StrEnum):
    FBR_INTEGRATION = "fbr_integration"
    FBR_INVOICING = "fbr_invoicing"


class UserNoteFieldsEnum(StrEnum):
    """
    Enumeration of customer fields.
    """

    ID = "id"
    USER_ID = "user_id"
    NOTE = "note"
    DEFAULT = "default"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
