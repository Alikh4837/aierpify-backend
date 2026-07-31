# src/auth/utils.py
from typing import Any, Dict, Optional

import jwt
from jwt.types import Options

from src.auth.constants import BASE64URL_PATTERN
from src.exceptions import InternalServerErrorException, UnauthorizedException


class JWTValidator:
    """
    JWT validator that uses cached JWKS for token validation.
    """

    def __init__(self, jwks_data: Dict[str, Any]):
        """
        Initialize the JWT validator with JWKS data.

        Args:
            jwks_data: The JWKS JSON data containing public keys
        """
        self.jwks_data = jwks_data
        # Create an in-memory JWKS client with the cached data
        self._signing_keys = self._build_signing_keys()

    def _build_signing_keys(self) -> Dict[str, Any]:
        """
        Build a dictionary of signing keys from JWKS data.

        Returns:
            Dictionary mapping key IDs to signing keys
        """
        signing_keys = {}
        for key_data in self.jwks_data.get("keys", []):
            kid = key_data.get("kid")
            if kid:
                # Convert JWK to a signing key using PyJWT
                signing_key = jwt.PyJWK(key_data)
                signing_keys[kid] = signing_key
        return signing_keys

    def _to_snake_case(self, s: str) -> str:
        """
        Convert a string from PascalCase or camelCase to snake_case.

        Args:
            s: The input string
        Returns:
            The converted snake_case string
        """

        snake = ""
        for i, char in enumerate(s):
            if char.isupper() and i != 0:
                snake += "_"
            snake += char.lower()
        return snake

    def is_jwt(self, token: str) -> bool:
        """
        Fast detection of JWT tokens without full decoding.

        Args:
            token: String that might be a JWT

        Returns:
            True if token appears to be a JWT, False otherwise
        """
        # Quick length check - JWTs are typically at least 100 chars
        if len(token) < 100:
            return False

        # Split on dots - must have exactly 3 parts
        parts = token.split(".")
        if len(parts) != 3:
            return False

        # Check each part is non-empty and base64url encoded
        for part in parts:
            if not part or not BASE64URL_PATTERN.match(part):
                return False

        # Optional: Verify header is reasonable length (20-60 chars typical)
        header_len = len(parts[0])
        if header_len < 20 or header_len > 100:
            return False

        return True

    def decode_token(
        self,
        token: str,
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
        algorithms: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Decode and validate a JWT token using the cached JWKS.

        Args:
            token: The JWT token to decode
            audience: Expected audience claim (optional)
            issuer: Expected issuer claim (optional)
            algorithms: List of allowed algorithms (defaults to ["RS256"])

        Returns:
            The decoded JWT payload as a dictionary

        Raises:
            UnauthorizedException: If token validation fails
        """
        if algorithms is None:
            algorithms = ["RS256", "HS256", "EdDSA"]

        try:
            # Get the key ID from the token header without verification
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise UnauthorizedException(detail="Token missing key ID (kid)")

            # Get the signing key for this token
            if kid not in self._signing_keys:
                raise UnauthorizedException(detail="Invalid token: unknown key ID")

            signing_key = self._signing_keys[kid]

            # Decode and verify the token
            options: Options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": audience is not None,
                "verify_iss": issuer is not None,
            }

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=algorithms,
                audience=audience,
                issuer=issuer,
                options=options,
            )

            # convert all keys in payload to snake case
            payload = {self._to_snake_case(k): v for k, v in payload.items()}

            return payload

        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(message="Token has expired")
        except jwt.InvalidTokenError as e:
            raise UnauthorizedException(message=f"Invalid token: {str(e)}")
        except Exception as e:
            raise InternalServerErrorException(
                message=f"Token validation failed: {str(e)}"
            )

    def refresh_keys(self, new_jwks_data: Dict[str, Any]) -> None:
        """
        Refresh the cached JWKS data with new keys.

        Args:
            new_jwks_data: New JWKS JSON data
        """
        self.jwks_data = new_jwks_data
        self._signing_keys = self._build_signing_keys()
