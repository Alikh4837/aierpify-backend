# -------------------------- Authentication Schemas -------------------------- #
from typing import Annotated, AsyncGenerator, Optional

from better_auth import (
    AdminApi,
    ApiClient,
    ApiKeyApi,
    Configuration,
    DefaultApi,
    JwtApi,
    UsernameApi,
)
from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from src.config import get_setting


class AuthClient(BaseModel):
    """
    Auth client for making requests to the authentication API. (BetterAuth)

    This Pydantic model wraps configured BetterAuth API clients. It accepts an
    access token (and optional host) at initialization and exposes set_token()
    to update the token/host afterwards.

    Attributes:
        client (ApiClient): The underlying API client instance.
        api (DefaultApi): The default API client for general authentication operations.
        admin (AdminApi): The admin API client for administrative authentication operations.
        api_key (ApiKeyApi): The API key API client for API key related operations.
        username (UsernameApi): The username API client for username related operations.
        jwt (JwtApi): The JWT API client for JWT related operations.
    """

    client: ApiClient
    api: DefaultApi
    admin: AdminApi
    api_key: ApiKeyApi
    username: UsernameApi
    jwt: JwtApi

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, token: Optional[str] = None, host: Optional[str] = None) -> None:
        config = Configuration()
        config.host = host or get_setting("BETTER_AUTH_URL", "http://localhost:8001")
        if token:
            config.access_token = token

        api_client = ApiClient(config)

        super().__init__(
            client=api_client,
            api=DefaultApi(api_client),
            admin=AdminApi(api_client),
            api_key=ApiKeyApi(api_client),
            username=UsernameApi(api_client),
            jwt=JwtApi(api_client),
        )
        self._config = config

    async def close(self) -> None:
        """
        Properly close the underlying ApiClient.
        """
        await self.client.close()

    async def set_token(self, token: str, host: Optional[str] = None) -> None:
        """
        Update the bearer token and optionally host.
        Old ApiClient is closed before creating a new one.
        """
        if host:
            self._config.host = host
        self._config.access_token = token

        # Close old client
        old_client = self.client
        if hasattr(old_client, "close"):
            try:
                await old_client.close()
            except Exception:
                pass

        # Recreate new client + APIs
        api_client = ApiClient(self._config)
        self.client = api_client
        self.api = DefaultApi(api_client)
        self.admin = AdminApi(api_client)
        self.api_key = ApiKeyApi(api_client)
        self.username = UsernameApi(api_client)
        self.jwt = JwtApi(api_client)


async def get_auth_client() -> AsyncGenerator[AuthClient, None]:
    """
    FastAPI dependency that creates an AuthClient per request
    and ensures cleanup after.
    """
    client = AuthClient()
    try:
        yield client
    finally:
        await client.close()


# -------------------------- Dependency Annotations -------------------------- #
AuthClientDep = Annotated[AuthClient, Depends(get_auth_client)]
