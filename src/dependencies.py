# src\dependencies.py

from typing import Annotated, Any, Dict, Optional

from fastapi import Depends

from src.auth.client import AuthClientDep
from src.auth.dependencies import (
    APIKeyDep,
    AuthHeaderDep,
    JWTValidatorDep,
)
from src.auth.models import User
from src.auth.user import AuthUser
from src.database import DBDep
from src.exceptions import (
    BadRequestException,
    UnauthorizedException,
)


# --------------------------- Dependency Functions --------------------------- #
async def auth_user_dependency(
    db_session: DBDep,
    auth_client: AuthClientDep,
    jwt_validator: JWTValidatorDep,
    api_key: APIKeyDep,
    authorization: AuthHeaderDep,
) -> AuthUser:
    """
    The Authenticated User dependency function that retrieves the authenticated user, profile, db session, and auth client.

    Returns:
        AuthUser: The authenticated user object containing user details, profile, db session, and auth client.
    """

    """
    The authentication dependency function that validates and retrieves the authenticated user.

    This function checks for authentication credentials in the following order:
    1. Session Cookie
    2. Authorization Header (Bearer Token)
    3. API Key Header

    Returns:
        Tuple[AuthClient, User]: A tuple containing the AuthClient and the authenticated User object.

    Raises:
        UnauthorizedException: If authentication fails or no valid credentials are provided.
        BadRequestException: If multiple authentication methods are provided.
    """

    # Initialize the auth token variables
    auth_token: Optional[str] = None
    # apikey_token: Optional[str] = None

    # Declare variables
    user: Optional[User] = None
    user_dict: Optional[Dict[str, Any]] = None

    # Count how many authentication methods are present
    auth_methods = sum([bool(authorization), bool(api_key)])

    # Check if more than one authentication method is provided
    if auth_methods > 1:
        raise BadRequestException(
            message="Ambiguous authentication! Provide only one authentication method.",
            extra={
                "methods": {
                    "authorization": bool(authorization),
                    "api_key": bool(api_key),
                }
            },
        )

    # Check if the Authorization credentials are present
    elif authorization:
        # Extract token from Bearer authentication
        auth_token = authorization.credentials

        if auth_token.startswith("Bearer "):
            auth_token = auth_token[len("Bearer ") :]

        # Check if the token is a session token or a JWT token
        if not jwt_validator.is_jwt(auth_token):
            # Session Token Flow
            # Set the auth token in the auth client
            await auth_client.set_token(auth_token)

            # Get user details using the token
            try:
                session_response = await auth_client.api.get_session()
            except Exception as e:
                raise UnauthorizedException(detail=f"{e}")

            # Extract user details from the response
            user_dict = session_response.user.model_dump(exclude={"image"})

        else:
            # JWT Token Flow
            # Decode and validate the JWT token using cached JWKS
            try:
                token_response = jwt_validator.decode_token(token=auth_token)

            except UnauthorizedException:
                # Re-raise authorization exceptions as-is
                raise
            except Exception as e:
                raise UnauthorizedException(detail=f"Token validation failed: {e}")

            user_dict = token_response

    elif api_key:
        raise NotImplementedError("API Key authentication not implemented yet")

    else:
        raise UnauthorizedException(detail="No authentication credentials provided")

    # Validate the response into a user object
    try:
        user = User.model_validate(user_dict)
    except Exception:
        raise UnauthorizedException(detail="Invalid user data in session")

    # TODO: Disabled preemptive profile creation and fetching, user profile should be manually created/fetched in relevant endpoints
    # # Get the user profile from the database session
    # query = select(UserProfile).where(UserProfile.user_id == user.id)
    # result = await db_session.exec(query)
    # db_profile = result.first()

    # if not db_profile:
    #     try:
    #         profile_obj = UserProfileBase(
    #             user_id=user.id, name=user.name, email=user.email
    #         )
    #         db_profile = UserProfile(**profile_obj.model_dump())
    #         db_session.add(db_profile)
    #         await db_session.commit()
    #         await db_session.refresh(db_profile)

    #     except Exception as e:
    #         raise InternalServerErrorException(
    #             message="Failed to create user profile", extra={"error": str(e)}
    #         )

    return AuthUser(user=user, session=db_session)


# -------------------------- Dependency Annotations -------------------------- #
AuthenticatedUser = Annotated[AuthUser, Depends(auth_user_dependency)]
