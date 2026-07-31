from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.client import AuthClient
from src.auth.models import User
from src.users.models import UserProfile


class AuthUser(BaseModel):
    """
    Authenticated user schema.

    Attributes:
        user (User): The authenticated user instance.
        session (AsyncSession): The database session for the request.
        profile (UserProfile): The user's profile instance.
        auth (AuthClient): The authentication client for making auth API requests.
    """

    user: User
    session: AsyncSession
    profile: Optional[UserProfile] = None
    auth: Optional[AuthClient] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
