#!/usr/bin/env bash
set -euo pipefail
cat > /app/auth_validator.py << 'PYEOF'
"""
JWT validator using HMAC-SHA256 with strict claim validation order and
timing-safe signature comparison.
"""
import base64
import hashlib
import hmac
import json
import time


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


class TokenValidator:
    def __init__(self, secret: str, issuer: str, audience: str) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience

    def _sign(self, header_payload: str) -> str:
        sig = hmac.new(
            self._secret.encode(),
            header_payload.encode(),
            hashlib.sha256
        ).digest()
        return _b64url_encode(sig)

    def validate(self, token: str) -> dict:
        """Validate token and return payload dict.

        Raises ValueError with specific messages:
        - "invalid token format" - not 3 parts
        - "invalid signature"    - HMAC mismatch
        - "token expired"        - exp check fails
        - "token not yet valid"  - nbf check fails
        - "invalid issuer"       - iss mismatch
        - "invalid audience"     - aud mismatch
        - "invalid subject"      - sub missing/invalid
        Raises RuntimeError if payload is not valid JSON.
        """
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("invalid token format")

        header_payload = f"{parts[0]}.{parts[1]}"
        expected_sig = self._sign(header_payload)

        # 1. Timing-safe signature comparison — MUST come before any payload inspection
        if not hmac.compare_digest(expected_sig, parts[2]):
            raise ValueError("invalid signature")

        try:
            payload = json.loads(_b64url_decode(parts[1]))
        except Exception:
            raise RuntimeError("invalid payload JSON")

        now = int(time.time())

        # 2. exp — token expiry (with 5-second clock skew tolerance)
        if 'exp' in payload:
            if payload['exp'] + 5 < now:
                raise ValueError("token expired")

        # 3. nbf — not-before (with 5-second clock skew tolerance)
        if 'nbf' in payload:
            if payload['nbf'] - 5 > now:
                raise ValueError("token not yet valid")

        # 4. iss — issuer
        if payload.get('iss') != self._issuer:
            raise ValueError("invalid issuer")

        # 5. aud — audience
        if payload.get('aud') != self._audience:
            raise ValueError("invalid audience")

        # 6. sub — subject (required, non-empty string, no null bytes)
        sub = payload.get('sub')
        if not sub or not isinstance(sub, str) or '\x00' in sub:
            raise ValueError("invalid subject")

        return payload

    def create_token(self, payload: dict) -> str:
        """Create a signed HS256 JWT token string."""
        header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = _b64url_encode(json.dumps(payload).encode())
        header_payload = f"{header}.{body}"
        sig = self._sign(header_payload)
        return f"{header_payload}.{sig}"
PYEOF
echo "Solution installed at /app/auth_validator.py"
