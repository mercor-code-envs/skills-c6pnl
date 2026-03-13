"""
JWT signing and timing-safe verification using HMAC-SHA256 and base64url encoding.
"""
import base64
import hashlib
import hmac
import json


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string, stripping '=' padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _b64url_decode(s: str) -> bytes:
    """Decode a base64url string, restoring padding as needed."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def sign(secret: str, header_payload: str) -> str:
    """
    Compute HMAC-SHA256 over header_payload and return as base64url (no padding).

    Args:
        secret:         The HMAC key as a plain string.
        header_payload: The string "{b64url_header}.{b64url_payload}".

    Returns:
        Base64url-encoded signature without '=' padding.
    """
    sig_bytes = hmac.new(
        secret.encode(),
        header_payload.encode(),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(sig_bytes)


def create_token(secret: str, payload: dict) -> str:
    """
    Create a signed HS256 JWT token.

    Args:
        secret:  HMAC key.
        payload: Dict of JWT claims.

    Returns:
        JWT string: "{header}.{payload}.{signature}"
    """
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload).encode())
    header_payload = f"{header}.{body}"
    sig = sign(secret, header_payload)
    return f"{header_payload}.{sig}"


def verify_signature(token: str, secret: str) -> dict:
    """
    Verify the HMAC-SHA256 signature of a JWT token using constant-time comparison.

    Args:
        token:  JWT string.
        secret: HMAC key.

    Returns:
        Decoded payload dict if signature is valid.

    Raises:
        ValueError: "invalid token format" or "invalid signature"
    """
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    header_payload = f"{parts[0]}.{parts[1]}"
    expected_sig = sign(secret, header_payload)

    # Timing-safe — do NOT use ==
    if not hmac.compare_digest(expected_sig, parts[2]):
        raise ValueError("invalid signature")

    return json.loads(_b64url_decode(parts[1]))
