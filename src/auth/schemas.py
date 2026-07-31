# src\auth\schemas.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import UUID as SQLUUID
from sqlmodel import (
    Boolean,
    Column,
    DateTime,
    Field,
    ForeignKey,
    Integer,
    SQLModel,
    Text,
    func,
)


# ---------------------------- Better Auth Schemas --------------------------- #
class UserBase(SQLModel):
    """
    A registered user of the application.

    Attributes:
        id (UUID): Unique identifier for the record.
        name (str): Unique login name for the user.
        email (str): Primary email address for the user.
        email_verified (bool): Whether the email address has been verified.
        image (Optional[str]): URL to the user's avatar or profile image.
        role (str): Authorization role for the user (e.g. "user", "admin").
        banned (bool): Flag indicating if the user is currently banned.
        ban_reason (Optional[str]): Optional textual reason for the ban.
        ban_expires (Optional[datetime]): Optional timestamp when the ban will expire.
        username (Optional[str]): Optional publicly visible username.
        display_username (Optional[str]): Optional formatted display name for UI presentation.
        isAnonymous (bool): Flag indicating if the user is anonymous.
        phone_number (Optional[str]): Optional phone number for the user.
        phone_number_verified (bool): Flag indicating if the phone number has been verified.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "user"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    name: str = Field(
        sa_column=Column("name", Text, unique=True, nullable=False, index=True),
        description="Unique login name for the user.",
    )
    email: str = Field(
        sa_column=Column("email", Text, unique=True, nullable=False, index=True),
        description="Primary email address for the user.",
    )
    email_verified: bool = Field(
        default=False,
        sa_column=Column("emailVerified", Boolean, nullable=False),
        description="Whether the email address has been verified.",
    )
    image: Optional[str] = Field(
        default=None,
        sa_column=Column("image", Text, nullable=True),
        description="URL to the user's avatar or profile image.",
    )
    role: Optional[str] = Field(
        default="user",
        sa_column=Column("role", Text, nullable=True),
        description='Authorization role for the user (e.g. "user", "admin").',
    )
    banned: Optional[bool] = Field(
        default=False,
        sa_column=Column("banned", Boolean, nullable=False),
        description="Flag indicating if the user is currently banned.",
    )
    ban_reason: Optional[str] = Field(
        default=None,
        sa_column=Column("banReason", Text, nullable=True),
        description="Optional textual reason for the ban.",
    )
    ban_expires: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "banExpires",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Optional timestamp when the ban will expire.",
    )
    username: Optional[str] = Field(
        default=None,
        sa_column=Column("username", Text, unique=True, nullable=True, index=True),
        description="Optional publicly visible username.",
    )
    display_username: Optional[str] = Field(
        default=None,
        sa_column=Column("displayUsername", Text, nullable=True),
        description="Optional formatted display name for UI presentation.",
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )

    is_anonymous: Optional[bool] = Field(
        default=False,
        sa_column=Column(
            "isAnonymous", Boolean, nullable=False, server_default="false"
        ),
        description="Flag indicating if the user is anonymous.",
    )

    phone_number: Optional[str] = Field(
        default=None,
        sa_column=Column("phoneNumber", Text, unique=True, nullable=True, index=True),
        description="Optional phone number for the user.",
    )

    phone_number_verified: Optional[bool] = Field(
        default=False,
        sa_column=Column("phoneNumberVerified", Boolean, nullable=True),
        description="Flag indicating if the phone number has been verified.",
    )

    # Supabase Compatibility Columns
    # DISABLED: These columns are commented out to avoid confusion, but can be enabled if Supabase compatibility is needed.
    # user_metadata: Optional[Dict] = Field(
    #     default_factory=dict,
    #     sa_column=Column("userMetadata", JSONB, nullable=True),
    #     description="Arbitrary user metadata stored as JSONB (Supabase compatibility).",
    # )

    # app_metadata: Optional[Dict] = Field(
    #     default_factory=dict,
    #     sa_column=Column("appMetadata", JSONB, nullable=True),
    #     description="Arbitrary app metadata stored as JSONB (Supabase compatibility).",
    # )

    # invited_at: datetime = Field(
    #     sa_column=Column(
    #         "invitedAt",
    #         DateTime(timezone=True),
    #         server_default=func.now(),
    #         nullable=False,
    #     ),
    #     description="Timestamp when the user was invited (Supabase compatibility).",
    # )

    # last_sign_in_at: datetime = Field(
    #     sa_column=Column(
    #         "lastSignInAt",
    #         DateTime(timezone=True),
    #         server_default=func.now(),
    #         onupdate=func.now(),
    #         nullable=False,
    #     ),
    #     description="Timestamp when the user last signed in (Supabase compatibility).",
    # )

    model_config = ConfigDict(extra="ignore")  # type: ignore


class SessionBase(SQLModel):
    """
    A user session tracking token and metadata.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this session.
        expires_at (datetime): Datetime when the session expires.
        token (str): Unique session token used for authenticating requests.
        ip_address (Optional[str]): IP address associated with the session.
        user_agent (Optional[str]): User agent string reported by the client.
        impersonated_by (Optional[str]): Optional user ID of the user performing impersonation.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "session"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    user_id: UUID = Field(
        sa_column=Column(
            "userId",
            SQLUUID,
            ForeignKey(column="user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="ID of the user who owns this session.",
    )
    expires_at: datetime = Field(
        sa_column=Column(
            "expiresAt",
            DateTime(timezone=True),
            nullable=False,
        ),
        description="Datetime when the session expires.",
    )
    token: str = Field(
        sa_column=Column("token", Text, unique=True, nullable=False, index=True),
        description="Unique session token used for authenticating requests.",
    )
    ip_address: Optional[str] = Field(
        default=None,
        sa_column=Column("ipAddress", Text, nullable=True),
        description="IP address associated with the session.",
    )
    user_agent: Optional[str] = Field(
        default=None,
        sa_column=Column("userAgent", Text, nullable=True),
        description="User agent string reported by the client.",
    )
    impersonated_by: Optional[str] = Field(
        default=None,
        sa_column=Column("impersonatedBy", Text, nullable=True),
        description="Optional user ID of the user performing impersonation.",
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )


class AccountBase(SQLModel):
    """
    External OAuth/provider account linked to a user.

    Attributes:
        id (UUID): Unique identifier for the record.
        account_id (UUID): Provider-specific account identifier.
        provider_id (UUID): Identifier of the external provider (e.g. "google").
        user_id (UUID): ID of the user this account belongs to.
        access_token (Optional[str]): Access token issued by the provider.
        refresh_token (Optional[str]): Refresh token issued by the provider.
        id_token (Optional[str]): ID token from OpenID Connect providers.
        access_token_expires_at (Optional[datetime]): Datetime when the access token expires.
        refresh_token_expires_at (Optional[datetime]): Datetime when the refresh token expires.
        scope (Optional[str]): Scopes granted to the access token (space-separated).
        password (Optional[str]): Optional hashed password for local authentication.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "account"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    account_id: UUID = Field(
        sa_column=Column("accountId", SQLUUID, nullable=False),
        description="Provider-specific account identifier.",
    )
    provider_id: str = Field(
        sa_column=Column("providerId", Text, nullable=False),
        description="Identifier of the external provider (e.g. 'google').",
    )
    user_id: UUID = Field(
        sa_column=Column(
            "userId",
            SQLUUID,
            ForeignKey(column="user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="ID of the user this account belongs to.",
    )
    access_token: Optional[str] = Field(
        default=None,
        sa_column=Column("accessToken", Text, nullable=True),
        description="Access token issued by the provider.",
    )
    refresh_token: Optional[str] = Field(
        default=None,
        sa_column=Column("refreshToken", Text, nullable=True),
        description="Refresh token issued by the provider.",
    )
    id_token: Optional[str] = Field(
        default=None,
        sa_column=Column("idToken", Text, nullable=True),
        description="ID token from OpenID Connect providers.",
    )
    access_token_expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "accessTokenExpiresAt",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Datetime when the access token expires.",
    )
    refresh_token_expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "refreshTokenExpiresAt",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Datetime when the refresh token expires.",
    )
    scope: Optional[str] = Field(
        default=None,
        sa_column=Column("scope", Text, nullable=True),
        description="Scopes granted to the access token (space-separated).",
    )
    password: Optional[str] = Field(
        default=None,
        sa_column=Column("password", Text, nullable=True),
        description="Optional hashed password for local authentication.",
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )


class VerificationBase(SQLModel):
    """
    One-time verification tokens used for email sign-in, password resets, etc.

    Attributes:
        id (UUID): Unique identifier for the record.
        identifier (str): Identifier for the verification (e.g. an email address).
        value (str): Verification token value.
        expires_at (datetime): Datetime when this verification token expires.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "verification"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    identifier: str = Field(
        sa_column=Column("identifier", Text, nullable=False),
        description="Identifier for the verification (e.g. an email address).",
    )
    value: str = Field(
        sa_column=Column("value", Text, nullable=False),
        description="Verification token value.",
    )
    expires_at: datetime = Field(
        sa_column=Column(
            "expiresAt",
            DateTime(timezone=True),
            nullable=False,
        ),
        description="Datetime when this verification token expires.",
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )


class APIKeyBase(SQLModel):
    """
    API key representing client credentials, usage limits and metadata.

    Attributes:
        id (UUID): Unique identifier for the record.
        user_id (UUID): ID of the user who owns this API key.
        name (Optional[str]): Human-friendly name for the API key.
        start (Optional[str]): Starting prefix for the API key.
        prefix (Optional[str]): Public prefix used to identify the key without revealing it.
        key (str): Secret API key value used to authenticate requests.
        refill_interval (Optional[int]): Interval (in seconds) for token bucket refill.
        refill_amount (Optional[int]): Number of tokens added on each refill.
        last_refill_at (Optional[datetime]): Datetime of the last refill event.
        enabled (Optional[bool]): Whether the API key is currently enabled.
        rate_limit_enabled (Optional[bool]): Whether request rate limiting is enabled for this key.
        rate_limit_time_window (Optional[int]): Rate limit time window in seconds.
        rate_limit_max (Optional[int]): Maximum number of requests allowed in the time window.
        request_count (Optional[int]): Current request count in the active rate window.
        remaining (Optional[int]): Remaining allowed requests in the current window.
        last_request (Optional[datetime]): Datetime of the last request made with this key.
        expires_at (Optional[datetime]): Optional expiration datetime for the API key.
        metadata_ (Optional[str]): Arbitrary metadata stored as JSON/string under the 'metadata' column.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "apikey"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    user_id: UUID = Field(
        sa_column=Column(
            "userId",
            SQLUUID,
            ForeignKey(column="user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="ID of the user who owns this API key.",
    )
    name: Optional[str] = Field(
        default=None,
        sa_column=Column("name", Text, nullable=True),
        description="Human-friendly name for the API key.",
    )
    start: Optional[str] = Field(
        default=None,
        sa_column=Column("start", Text, nullable=True),
        description="Starting prefix for the API key.",
    )
    prefix: Optional[str] = Field(
        default=None,
        sa_column=Column("prefix", Text, nullable=True),
        description="Public prefix used to identify the key without revealing it.",
    )
    key: str = Field(
        sa_column=Column("key", Text, nullable=False),
        description="Secret API key value used to authenticate requests.",
    )
    refill_interval: Optional[int] = Field(
        default=None,
        sa_column=Column("refillInterval", Integer, nullable=True),
        description="Interval (in seconds) for token bucket refill.",
    )
    refill_amount: Optional[int] = Field(
        default=None,
        sa_column=Column("refillAmount", Integer, nullable=True),
        description="Number of tokens added on each refill.",
    )
    last_refill_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "lastRefillAt",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Datetime of the last refill event.",
    )
    enabled: Optional[bool] = Field(
        default=None,
        sa_column=Column("enabled", Text, nullable=True),
        description="Whether the API key is currently enabled.",
    )
    rate_limit_enabled: Optional[bool] = Field(
        default=None,
        sa_column=Column("rateLimitEnabled", Text, nullable=True),
        description="Whether request rate limiting is enabled for this key.",
    )
    rate_limit_time_window: Optional[int] = Field(
        default=None,
        sa_column=Column("rateLimitTimeWindow", Integer, nullable=True),
        description="Rate limit time window in seconds.",
    )
    rate_limit_max: Optional[int] = Field(
        default=None,
        sa_column=Column("rateLimitMax", Integer, nullable=True),
        description="Maximum number of requests allowed in the time window.",
    )
    request_count: Optional[int] = Field(
        default=None,
        sa_column=Column("requestCount", Integer, nullable=True),
        description="Current request count in the active rate window.",
    )
    remaining: Optional[int] = Field(
        default=None,
        sa_column=Column("remaining", Integer, nullable=True),
        description="Remaining allowed requests in the current window.",
    )
    last_request: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "lastRequest",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Datetime of the last request made with this key.",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "expiresAt",
            DateTime(timezone=True),
            nullable=True,
        ),
        description="Optional expiration datetime for the API key.",
    )
    permissions: Optional[str] = Field(
        default=None,
        sa_column=Column("permissions", Text, nullable=True),
        description="Optional string of permissions/scopes assigned to this key.",
    )
    metadata_: Optional[str] = Field(
        default=None,
        alias="metadata",
        sa_column=Column("metadata", Text, nullable=True),
        description="Arbitrary metadata stored as JSON/string under the 'metadata' column.",
        schema_extra={
            "serialization_alias": "metadata",
            "validation_alias": "metadata",
        },
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )


class JWKBase(SQLModel):
    """
    JSON Web Key pair used for signing and verifying tokens.

    Attributes:
        id (UUID): Unique identifier for the record.
        public_key (str): Public key material (PEM or JWK).
        private_key (str): Private key material (PEM or JWK), kept secure.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "jwks"  # type: ignore

    id: UUID = Field(
        sa_column=Column("id", SQLUUID, primary_key=True, nullable=False, index=True),
    )
    public_key: str = Field(
        sa_column=Column("publicKey", Text, nullable=False),
        description="Public key material used to verify signatures.",
    )
    private_key: str = Field(
        sa_column=Column("privateKey", Text, nullable=False),
        description="Private key material used to sign tokens (store securely).",
    )
    created_at: datetime = Field(
        sa_column=Column(
            "createdAt",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updatedAt",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the record was last updated.",
    )
