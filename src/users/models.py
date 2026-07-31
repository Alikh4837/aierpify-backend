# src\users\models.py
from src.models import DBIDMixin
from src.schemas import TimestampMixin
from src.users.schemas import (
    FBRProfileBase,
    SubscriptionPlanBase,
    UserNoteBase,
    UserPlanBase,
    UserProfileBase,
)


# -------------------------------- User Models ------------------------------- #
class UserProfile(TimestampMixin, UserProfileBase, DBIDMixin, table=True):
    """
    Profile information for a user, stored in the database.
    Inherits all fields from UserProfileBase.
    """

    pass


class FBRProfile(TimestampMixin, FBRProfileBase, DBIDMixin, table=True):
    """
    FBR (Federal Board of Revenue) profile details for a user's business, stored in the database.
    Inherits all fields from FBRProfileBase.
    """

    pass


class SubscriptionPlan(TimestampMixin, SubscriptionPlanBase, DBIDMixin, table=True):
    """
    Available subscription plans with feature limits, stored in the database.
    Inherits all fields from SubscriptionPlanBase.
    """

    pass


class UserPlan(TimestampMixin, UserPlanBase, DBIDMixin, table=True):
    """
    The subscription plan a user is currently subscribed to, stored in the database.
    Inherits all fields from UserPlanBase.
    """

    pass


class UserNote(TimestampMixin, UserNoteBase, DBIDMixin, table=True):
    """
    Notes associated with a user, stored in the database.
    Inherits all fields from UserNoteBase.
    """

    pass
