class TokenValidator:
    def __init__(self, secret: str, issuer: str, audience: str) -> None:
        pass

    def validate(self, token: str) -> dict:
        """Validate token and return the payload on success.
        Raises ValueError with these exact messages on failure:
        - "invalid token format"
        - "invalid signature"
        - "token expired"
        - "token not yet valid"
        - "invalid issuer"
        - "invalid audience"
        - "invalid subject"
        """
        pass

    def create_token(self, payload: dict) -> str:
        """Create a signed HS256 JWT token."""
        pass
