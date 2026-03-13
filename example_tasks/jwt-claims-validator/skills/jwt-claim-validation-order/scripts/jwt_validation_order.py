"""
JWT claim validation with the correct order and 5-second clock skew tolerance.

Validation sequence: signature → exp → nbf → iss → aud → sub
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


class JWTValidator:
    CLOCK_SKEW = 5  # seconds

    def __init__(self, secret: str, issuer: str, audience: str) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience

    def _sign(self, header_payload: str) -> str:
        sig = hmac.new(
            self._secret.encode(),
            header_payload.encode(),
            hashlib.sha256,
        ).digest()
        return _b64url_encode(sig)

    def validate(self, token: str) -> dict:
        # 1. Format check
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("invalid token format")

        # 2. Signature — MUST be first payload check
        header_payload = f"{parts[0]}.{parts[1]}"
        expected_sig = self._sign(header_payload)
        if not hmac.compare_digest(expected_sig, parts[2]):
            raise ValueError("invalid signature")

        payload = json.loads(_b64url_decode(parts[1]))
        now = int(time.time())

        # 3. exp — expiry with clock skew
        if 'exp' in payload:
            if payload['exp'] + self.CLOCK_SKEW < now:
                raise ValueError("token expired")

        # 4. nbf — not-before with clock skew
        if 'nbf' in payload:
            if payload['nbf'] - self.CLOCK_SKEW > now:
                raise ValueError("token not yet valid")

        # 5. iss
        if payload.get('iss') != self._issuer:
            raise ValueError("invalid issuer")

        # 6. aud
        if payload.get('aud') != self._audience:
            raise ValueError("invalid audience")

        # 7. sub
        sub = payload.get('sub')
        if not sub or not isinstance(sub, str) or '\x00' in sub:
            raise ValueError("invalid subject")

        return payload

    def create_token(self, payload: dict) -> str:
        header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = _b64url_encode(json.dumps(payload).encode())
        header_payload = f"{header}.{body}"
        return f"{header_payload}.{self._sign(header_payload)}"
