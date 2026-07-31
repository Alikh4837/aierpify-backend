# src\users\schemas.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, NonNegativeFloat
from sqlmodel import ARRAY, TEXT, AutoString, Column, DateTime, Field, SQLModel, func

from src.enums import ProvinceEnum
from src.schemas import (
    DeleteRequestMixin,
    DeleteResponseMixin,
    IDMixin,
    OptionalIDMixin,
    OptionalUserIDMixin,
    TimestampMixin,
)
from src.users.enums import SubscriptionPlanFeaturesEnum, SubscriptionPlanPeriodEnum


# ---------------------------------------------------------------------------- #
#                                 Base Schemas                                 #
# ---------------------------------------------------------------------------- #
class UserProfileBase(SQLModel):
    """
    User profile with basic information.

    Attributes:
        user_id (UUID): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        logo_url (Optional[str]): Business logo image URL.
    """

    __tablename__ = "user_profiles"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        unique=True,
        nullable=False,
        description="ID of the user this profile belongs to.",
    )
    name: str = Field(
        index=True,
        nullable=False,
        description="Name of the user's business.",
    )
    email: Optional[str] = Field(
        index=True,
        default=None,
        nullable=True,
        description="Business contact email address.",
    )
    phone: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Business contact phone number.",
    )
    address: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Physical address of the business.",
    )
    province: Optional[ProvinceEnum] = Field(
        default=None,
        description="Province where the business is located.",
        sa_column=Column("province", AutoString, nullable=True),
    )
    logo_url: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Business logo image URL.",
    )


class FBRProfileBase(SQLModel):
    """
    FBR (Federal Board of Revenue) profile details for a user's business.

    Attributes:
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
    """

    __tablename__ = "fbr_profiles"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        unique=True,
        nullable=False,
        description="ID of the user this FBR profile belongs to.",
    )
    sandbox_token: str = Field(
        nullable=False,
        description="FBR sandbox integration token.",
    )
    production_token: str = Field(
        nullable=False,
        description="FBR production integration token.",
    )
    national_tax_number: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Business National Tax Number.",
    )
    sales_tax_registration_number: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Business Sales Tax Registration Number.",
    )
    integration_validated: bool = Field(
        default=False,
        nullable=False,
        description="Whether FBR integration has been validated.",
    )
    invoicing_enabled: bool = Field(
        default=False,
        nullable=False,
        description="Whether invoicing via FBR is enabled.",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether this FBR profile is currently active.",
    )


class SubscriptionPlanBase(SQLModel):
    """
    Available subscription plans with feature limits.

    Attributes:
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (int): Maximum number of customers allowed.
        products_limit (int): Maximum number of products allowed.
        invoices_limit (int): Maximum number of invoices allowed.
        features (str): JSON string object containing plan features.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
    """

    __tablename__ = "subscription_plans"  # type: ignore

    name: str = Field(
        index=True,
        nullable=False,
        description="Name of the subscription plan.",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Description of the plan features.",
    )
    price: NonNegativeFloat = Field(
        nullable=False,
        description="Price of the subscription plan.",
    )
    billing_period: SubscriptionPlanPeriodEnum = Field(
        default=SubscriptionPlanPeriodEnum.MONTHLY,
        description="Billing frequency.",
        sa_column=Column("billing_period", AutoString, nullable=False),
    )
    usage_period: SubscriptionPlanPeriodEnum = Field(
        default=SubscriptionPlanPeriodEnum.MONTHLY,
        description="Usage period for feature limits.",
        sa_column=Column(
            "usage_period", AutoString, nullable=False, server_default="monthly"
        ),
    )
    customers_limit: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Maximum number of customers allowed.",
    )
    products_limit: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Maximum number of products allowed.",
    )
    invoices_limit: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Maximum number of invoices allowed.",
    )
    features: list[SubscriptionPlanFeaturesEnum] = Field(
        default=[],
        description="Features included in the subscription plan.",
        sa_column=Column("features", ARRAY(TEXT), nullable=False),
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether the plan is currently available for purchase.",
    )
    limits_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether the feature limits are currently enforced.",
    )

    model_config = ConfigDict(use_enum_values=True)  # type: ignore


class UserPlanBase(SQLModel):
    """
    Current usage and limits for a user's subscription.

    Attributes:
        user_id (UUID): ID of the user this subscription limit applies to.
        plan_id (UUID): ID of the current subscription plan.
        start_date (datetime): When the current subscription started.
        auto_renew (bool): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (int): Number of customers currently used.
        products_used (int): Number of products currently used.
        invoices_used (int): Number of invoices currently used.
    """

    __tablename__ = "user_plans"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the user this subscription limit applies to.",
    )
    plan_id: UUID = Field(
        foreign_key="subscription_plans.id",
        ondelete="RESTRICT",
        nullable=True,
        description="ID of the current subscription plan.",
    )
    start_date: datetime = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"server_default": func.now()},
        description="When the current subscription started.",
    )
    auto_renew: bool = Field(
        default=False,
        description="Whether the subscription is set to auto-renew at the end of the current billing period.",
        sa_column_kwargs={"server_default": "false"},
    )
    customers_used: int = Field(
        default=0,
        nullable=True,
        description="Number of customers currently used.",
    )
    products_used: int = Field(
        default=0,
        nullable=True,
        description="Number of products currently used.",
    )
    invoices_used: int = Field(
        default=0,
        nullable=True,
        description="Number of invoices currently used.",
    )


class UserNoteBase(SQLModel):
    """
    User notes for use with invoices and other records.

    Attributes:
        user_id (UUID): ID of the user this note belongs to.
        note (str): The content of the note.
        default (bool): Indicates if this note is the default note for the user.
    """

    __tablename__ = "user_notes"  # type: ignore

    user_id: UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        nullable=False,
        description="ID of the user this note belongs to.",
    )
    note: str = Field(
        nullable=False,
        description="The content of the note.",
    )
    default: bool = Field(
        default=False,
        nullable=False,
        unique=True,  # Ensures only one default note per user
        description="Indicates if this note is the default note for the user.",
    )


# ---------------------------------------------------------------------------- #
#                             Endpoint I/O Schemas                             #
# ---------------------------------------------------------------------------- #
# -------------------------------- UserProfile ------------------------------- #
class UserProfileResponse(TimestampMixin, UserProfileBase, IDMixin):
    """
    Response model for user profile details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        logo_url (Optional[str]): Business logo image URL.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UserProfileResponseList(SQLModel):
    """
    Response model for a list of user profiles.

    Attributes:
        data (List[UserProfileResponse]): List of user profiles.
    """

    data: List[UserProfileResponse] = Field(
        default=[],
        description="List of user profile responses.",
    )


class CreateUserProfileRequest(UserProfileBase):
    """
    Request model for creating a new user profile.

    Attributes:
        user_id (Optional[UUID]): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        logo_url (Optional[str]): Business logo image URL.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this profile belongs to."
    )


class CreateUserProfileResponse(UserProfileResponse):
    """
    Response model for creating a new user profile.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetUserProfileRequest(OptionalUserIDMixin, OptionalIDMixin):
    """
    Request model for retrieving a user profile with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this profile belongs to.
    """

    pass


class GetUserProfileResponse(UserProfileResponse):
    """
    Response model for retrieving user profiles.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetUserProfilesRequest(GetUserProfileRequest):
    """
    Request model for retrieving multiple user profiles with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this profile belongs to.
    """

    pass


class GetUserProfilesResponse(UserProfileResponseList):
    """
    Response model for retrieving multiple user profiles.

    Attributes:
        data (List[UserProfileResponse]): List of user profiles.
    """

    pass


class UpdateUserProfileRequest(UserProfileBase):
    """
    Request model for updating an existing user profile.

    Attributes:
        user_id (Optional[UUID]): ID of the user this profile belongs to.
        name (Optional[str]): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        logo_url (Optional[str]): Business logo image URL.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this profile belongs to."
    )
    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the user's business."
    )


class UpdateUserProfileResponse(UserProfileResponse):
    """
    Response model for updating an existing user profile.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this profile belongs to.
        name (str): Name of the user's business.
        email (Optional[str]): Business contact email address.
        phone (Optional[str]): Business contact phone number.
        address (Optional[str]): Physical address of the business.
        province (Optional[ProvinceEnum]): Province where the business is located.
        logo_url (Optional[str]): Business logo image URL.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


# -------------------------------- FBRProfile -------------------------------- #
class FBRProfileResponse(TimestampMixin, FBRProfileBase, IDMixin):
    """
    Response model for FBR profile details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class FBRProfilePublicResponse(SQLModel):
    """
    Public Response model for FBR profile details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    id: UUID = Field(
        description="Unique identifier for the record.",
    )
    user_id: UUID = Field(
        description="ID of the user this FBR profile belongs to.",
    )
    national_tax_number: Optional[str] = Field(
        default=None,
        description="Business National Tax Number.",
    )
    sales_tax_registration_number: Optional[str] = Field(
        default=None,
        description="Business Sales Tax Registration Number.",
    )
    created_at: datetime = Field(
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        description="Timestamp when the record was last updated.",
    )


class CreateFBRProfileRequest(FBRProfileBase):
    """
    Request model for creating a new FBR profile.

    Attributes:
        user_id (Optional[UUID]): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this FBR profile belongs to."
    )


class CreateFBRProfileResponse(FBRProfileResponse):
    """
    Response model for creating a new FBR profile.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetFBRProfileRequest(OptionalUserIDMixin, OptionalIDMixin):
    """
    Request model for retrieving an FBR profile with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this FBR profile belongs to.
    """

    pass


class GetFBRProfileResponse(FBRProfileResponse):
    """
    Response model for retrieving FBR profiles.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UpdateFBRProfileRequest(FBRProfileBase):
    """
    Request model for updating an existing FBR profile.

    Attributes:
        user_id (Optional[UUID]): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (Optional[str]): FBR sandbox integration token.
        production_token (Optional[str]): FBR production integration token.
        integration_validated (Optional[bool]): Whether FBR integration has been validated.
        invoicing_enabled (Optional[bool]): Whether invoicing via FBR is enabled.
        is_active (Optional[bool]): Whether this FBR profile is currently active.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this FBR profile belongs to."
    )
    sandbox_token: Optional[str] = Field(  # type: ignore[override]
        default=None, description="FBR sandbox integration token."
    )
    production_token: Optional[str] = Field(  # type: ignore[override]
        default=None, description="FBR production integration token."
    )
    integration_validated: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether FBR integration has been validated."
    )
    invoicing_enabled: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether invoicing via FBR is enabled."
    )
    is_active: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Whether this FBR profile is currently active."
    )


class UpdateFBRProfileResponse(FBRProfileResponse):
    """
    Response model for updating an existing FBR profile.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this FBR profile belongs to.
        national_tax_number (Optional[str]): Business National Tax Number.
        sales_tax_registration_number (Optional[str]): Business Sales Tax Registration Number.
        sandbox_token (str): FBR sandbox integration token.
        production_token (str): FBR production integration token.
        integration_validated (bool): Whether FBR integration has been validated.
        invoicing_enabled (bool): Whether invoicing via FBR is enabled.
        is_active (bool): Whether this FBR profile is currently active.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


# ----------------------------- SubscriptionPlan ----------------------------- #
class SubscriptionPlanResponse(TimestampMixin, SubscriptionPlanBase, IDMixin):
    """
    Response model for subscription plan details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (str): JSON string object containing plan features.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class CreateSubscriptionPlanRequest(SubscriptionPlanBase):
    """
    Request model for creating a new subscription plan.

    Attributes:
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (str): JSON string object containing plan features.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
    """

    pass


class CreateSubscriptionPlanResponse(SubscriptionPlanResponse):
    """
    Response model for creating a new subscription plan.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (str): JSON string object containing plan features.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetSubscriptionPlanRequest(OptionalIDMixin):
    """
    Request model for retrieving a subscription plan with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
    """

    pass


class GetSubscriptionPlanResponse(SubscriptionPlanResponse):
    """
    Response model for retrieving subscription plans.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (str): JSON string object containing plan features.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UpdateSubscriptionPlanRequest(SubscriptionPlanBase, IDMixin):
    """
    Request model for updating an existing subscription plan.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (Optional[str]): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (Optional[NonNegativeFloat]): Price of the subscription plan.
        billing_period (Optional[SubscriptionPlanPeriodEnum]): Billing frequency.
        usage_period (Optional[SubscriptionPlanPeriodEnum]): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (Optional[List[SubscriptionPlanFeaturesEnum]]): List of features included in the subscription plan.
        is_active (Optional[bool]): Whether the plan is currently available for purchase.
        limits_active (Optional[bool]): Whether the feature limits are currently enforced.
    """

    name: Optional[str] = Field(  # type: ignore[override]
        default=None, description="Name of the subscription plan."
    )
    price: Optional[NonNegativeFloat] = Field(  # type: ignore[override]
        default=None, description="Price of the subscription plan."
    )
    billing_period: Optional[SubscriptionPlanPeriodEnum] = Field(  # type: ignore[override]
        default=None, description="Billing frequency."
    )
    usage_period: Optional[SubscriptionPlanPeriodEnum] = Field(  # type: ignore[override]
        default=None, description="Usage period for feature limits."
    )
    features: Optional[list[SubscriptionPlanFeaturesEnum]] = Field(  # type: ignore[override]
        default=None, description="List of features included in the subscription plan."
    )
    is_active: Optional[bool] = Field(  # type: ignore[override]
        default=None,
        description="Whether the plan is currently available for purchase.",
    )
    limits_active: Optional[bool] = Field(  # type: ignore[override]
        default=None,
        description="Whether the feature limits are currently enforced.",
    )


class UpdateSubscriptionPlanResponse(SubscriptionPlanResponse):
    """
    Response model for updating an existing subscription plan.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (str): Name of the subscription plan.
        description (Optional[str]): Description of the plan features.
        price (NonNegativeFloat): Price of the subscription plan.
        billing_period (SubscriptionPlanPeriodEnum): Billing frequency.
        usage_period (SubscriptionPlanPeriodEnum): Usage period for feature limits.
        customers_limit (Optional[int]): Maximum number of customers allowed.
        products_limit (Optional[int]): Maximum number of products allowed.
        invoices_limit (Optional[int]): Maximum number of invoices allowed.
        features (List[SubscriptionPlanFeaturesEnum]): List of features included in the subscription plan.
        is_active (bool): Whether the plan is currently available for purchase.
        limits_active (bool): Whether the feature limits are currently enforced.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class DeleteSubscriptionPlanRequest(DeleteRequestMixin):
    """
    Request model for deleting a subscription plan by ID.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
    """

    pass


class DeleteSubscriptionPlanResponse(DeleteResponseMixin):
    """
    Response model for deleting a subscription plan.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass


# --------------------------------- UserPlan --------------------------------- #
class UserPlanResponse(TimestampMixin, UserPlanBase, IDMixin):
    """
    Response model for user subscription plan details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this subscription limit applies to.
        plan_id (UUID): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        auto_renew (bool): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UserPlanResponseList(SQLModel):
    """
    Response model for a list of user subscription plans.

    Attributes:
        data (List[UserPlanResponse]): List of user subscription plans.
    """

    data: List[UserPlanResponse] = Field(
        default=[],
        description="List of user plan responses.",
    )


class CreateUserPlanRequest(UserPlanBase):
    """
    Request model for creating a new user plan.

    Attributes:
        user_id (Optional[UUID]): ID of the user this subscription limit applies to.
        plan_id (Optional[UUID]): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        auto_renew (Optional[bool]): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this subscription limit applies to."
    )


class CreateUserPlanResponse(UserPlanResponse):
    """
    Response model for creating a new user plan, including the associated subscription plan.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this subscription limit applies to.
        plan_id (UUID): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        auto_renew (bool): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
        subscription_plan (SubscriptionPlanResponse): Details of the subscription plan.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    subscription_plan: SubscriptionPlanResponse


class GetUserPlanRequest(OptionalUserIDMixin, OptionalIDMixin):
    """
    Request model for retrieving a user plan with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this subscription limit applies to.
    """

    pass


class GetUserPlanResponse(UserPlanResponse):
    """
    Response model for retrieving user plans.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this subscription limit applies to.
        plan_id (UUID): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
        subscription_plan (Optional[SubscriptionPlanResponse]): Details of the subscription plan.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    subscription_plan: Optional[SubscriptionPlanResponse] = Field(
        default=None, description="Details of the subscription plan."
    )


class GetUserPlansRequest(GetUserPlanRequest):
    """
    Request model for retrieving multiple user plans with optional filtering by ID.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this subscription limit applies to.
    """

    pass


class GetUserPlansResponse(UserPlanResponseList):
    """
    Response model for retrieving multiple user subscription plans.

    Attributes:
        data (List[UserPlanResponse]): List of user subscription plans.
    """

    pass


class UpdateUserPlanRequest(UserPlanBase):
    """
    Request model for updating an existing user plan.

    Attributes:
        user_id (Optional[UUID]): ID of the user this subscription limit applies to.
        plan_id (Optional[UUID]): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        auto_renew (Optional[bool]): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this subscription limit applies to."
    )
    plan_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the current subscription plan."
    )
    start_date: Optional[datetime] = Field(  # type: ignore[override]
        default=None,
        description="When the current subscription started.",
    )
    auto_renew: Optional[bool] = Field(  # type: ignore[override]
        default=None,
        description="Whether the subscription is set to auto-renew at the end of the current billing period.",
    )
    customers_used: Optional[int] = Field(  # type: ignore[override]
        default=None,
        nullable=True,
        description="Number of customers currently used.",
    )
    products_used: Optional[int] = Field(  # type: ignore[override]
        default=None,
        nullable=True,
        description="Number of products currently used.",
    )
    invoices_used: Optional[int] = Field(  # type: ignore[override]
        default=None,
        nullable=True,
        description="Number of invoices currently used.",
    )


class UpdateUserPlanResponse(UserPlanResponse):
    """
    Response model for updating an existing user plan.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this subscription limit applies to.
        plan_id (UUID): ID of the current subscription plan.
        start_date (Optional[datetime]): When the current subscription started.
        auto_renew (bool): Whether the subscription is set to auto-renew at the end of the current billing period.
        customers_used (Optional[int]): Number of customers currently used.
        products_used (Optional[int]): Number of products currently used.
        invoices_used (Optional[int]): Number of invoices currently used.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


# --------------------------------- UserNote -------------------------------- #
class UserNoteResponse(TimestampMixin, UserNoteBase, IDMixin):
    """
    Response model for user notes details, including ID and timestamps.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this note belongs to.
        note (str): The content of the note.
        default (bool): Indicates if this note is the default note for the user.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class CreateUserNoteRequest(UserNoteBase):
    """
    Request model for creating a new user note.

    Attributes:
        user_id (Optional[UUID]): ID of the user this note belongs to.
        note (str): The content of the note.
        default (Optional[bool]): Indicates if this note is the default note for the user.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this note belongs to."
    )
    default: Optional[bool] = Field(  # type: ignore[override]
        default=None,
        description="Indicates if this note is the default note for the user.",
    )


class CreateUserNoteResponse(UserNoteResponse):
    """
    Response model for creating a new user note.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this note belongs to.
        note (str): The content of the note.
        default (bool): Indicates if this note is the default note for the user.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class GetUserNoteRequest(OptionalUserIDMixin, IDMixin):
    """
    Request model for retrieving a user note with optional filtering by ID.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this note belongs to.
    """

    pass


class GetUserNoteResponse(UserNoteResponse):
    """
    Response model for retrieving user notes.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user this note belongs to.
        note (str): The content of the note.
        default (bool): Indicates if this note is the default note for the user.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    pass


class UserNoteResponseList(SQLModel):
    """
    Response model for retrieving multiple user notes.

    Attributes:
        notes (List[UserNoteResponse]): List of user notes.
    """

    data: List[UserNoteResponse] = Field(default=[], description="List of user notes.")


class GetUserNotesRequest(
    UserNoteBase,
    OptionalIDMixin,
):
    """
    Request model for retrieving multiple user notes with pagination.

    Attributes:
        id (Optional[UUID]): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this note belongs to.
        note (Optional[str]): The content of the note.
        default (Optional[bool]): Filter for default notes.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this note belongs to."
    )
    note: Optional[str] = Field(  # type: ignore[override]
        default=None, description="The content of the note."
    )
    default: Optional[bool] = Field(  # type: ignore[override]
        default=None, description="Filter for default notes."
    )


class GetUserNotesResponse(SQLModel):
    """
    Response model for retrieving multiple user notes with pagination.

    Attributes:
        notes (List[UserNoteResponse]): List of user notes.
    """

    data: List[UserNoteResponse] = Field(default=[], description="List of user notes.")


class UpdateUserNoteRequest(UserNoteBase, IDMixin):
    """
    Request model for updating an existing user note.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (Optional[UUID]): ID of the user this note belongs to.
        note (Optional[str]): The content of the note.
        default (Optional[bool]): Indicates if this note is the default note for the user.
    """

    user_id: Optional[UUID] = Field(  # type: ignore[override]
        default=None, description="ID of the user this note belongs to."
    )
    note: Optional[str] = Field(  # type: ignore[override]
        default=None, description="The content of the note."
    )
    default: Optional[bool] = Field(  # type: ignore[override]
        default=None,
        description="Indicates if this note is the default note for the user.",
    )


class UpdateUserNoteResponse(UserNoteResponse):
    """
    Response model for updating an existing user note.
    """

    pass


class DeleteUserNoteRequest(DeleteRequestMixin):
    """
    Request model for deleting user notes by ID.

    Attributes:
        id (List[UUID]): Unique identifiers for the records to be deleted.
    """

    pass


class DeleteUserNoteResponse(DeleteResponseMixin):
    """
    Response model for deleting user notes.

    Attributes:
        message (str): Message about the deletion.
        detail (Optional[Any]): Additional detail about the deletion.
    """

    pass
