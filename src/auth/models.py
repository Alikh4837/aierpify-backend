# src\auth\models.py
from src.auth.schemas import (
    AccountBase,
    APIKeyBase,
    JWKBase,
    SessionBase,
    UserBase,
    VerificationBase,
)


# ---------------------------- Better Auth Models ---------------------------- #
class User(UserBase, table=True):
    """
    A registered user of the application, stored in the database.
    Inherits all fields from UserBase.
    """

    pass


class Session(SessionBase, table=True):
    """
    A user session tracking token and metadata, stored in the database.
    Inherits all fields from SessionBase.
    """

    pass


class Account(AccountBase, table=True):
    """
    External OAuth/provider account linked to a user, stored in the database.
    Inherits all fields from AccountBase.
    """

    pass


class Verification(VerificationBase, table=True):
    """
    One-time verification tokens used for email sign-in, password resets, etc., stored in the database.
    Inherits all fields from VerificationBase.
    """

    pass


class APIKey(APIKeyBase, table=True):
    """
    API key representing client credentials, usage limits and metadata, stored in the database.
    Inherits all fields from APIKeyBase.
    """

    pass


class JWK(JWKBase, table=True):
    """
    JSON Web Key pair used for signing and verifying tokens, stored in the database.
    Inherits all fields from JWKBase.
    """

    pass
