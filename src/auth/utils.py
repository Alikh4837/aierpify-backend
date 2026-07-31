from src.config import get_setting


def get_jwks_data() -> dict:
    """
    Fetches JWKS data from the auth server.

    This function is used during application startup to cache the JWKS data for JWT validation.

    Returns:
        dict: The JWKS data retrieved from the auth server.
    """
    keys = []

    # Build keys list from settings
    key_config = {
        "alg": get_setting("BETTER_AUTH_JWKS_ALG"),
        "crv": get_setting("BETTER_AUTH_JWKS_CRV"),
        "kty": get_setting("BETTER_AUTH_JWKS_KTY"),
        "x": get_setting("BETTER_AUTH_JWKS_X"),
        "kid": get_setting("BETTER_AUTH_JWKS_KID"),
    }
    keys.append(key_config)

    jwks_data = {"keys": keys}
    return jwks_data
