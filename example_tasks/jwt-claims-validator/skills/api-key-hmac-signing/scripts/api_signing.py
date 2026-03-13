"""
HMAC-SHA256 signing for REST API requests using an API key.
"""
import hashlib
import hmac
import time


def canonical_request(method: str, path: str, body: bytes, timestamp: int) -> str:
    """Build the canonical string to sign."""
    body_hash = hashlib.sha256(body).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{body_hash}"


def sign_request(
    api_key: str,
    api_secret: str,
    method: str,
    path: str,
    body: bytes = b'',
) -> dict:
    """
    Sign an API request. Returns HTTP headers to include.
    """
    timestamp = int(time.time())
    canonical = canonical_request(method, path, body, timestamp)
    sig = hmac.new(
        api_secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).digest().hex()

    return {
        'X-API-Key': api_key,
        'X-Timestamp': str(timestamp),
        'X-Signature': sig,
    }


def verify_request(
    api_secret: str,
    method: str,
    path: str,
    body: bytes,
    timestamp: int,
    provided_sig: str,
    max_age_seconds: int = 300,
) -> bool:
    """
    Verify a signed API request.

    Returns True if signature is valid and request is fresh.
    """
    now = int(time.time())
    if abs(now - timestamp) > max_age_seconds:
        return False

    canonical = canonical_request(method, path, body, timestamp)
    expected = hmac.new(
        api_secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).digest().hex()

    return hmac.compare_digest(expected, provided_sig)
