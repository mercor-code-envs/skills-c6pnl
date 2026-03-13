---
name: api-key-hmac-signing
description: >
  HMAC-SHA256 signing for REST API requests using an API key. Covers canonical
  request construction (method + path + timestamp + body hash), signature
  format, and replay attack prevention with request timestamps. Designed for
  service-to-service authentication, not JWT token format.
---

# API Key HMAC Request Signing

## What is API Key HMAC Signing?

API key HMAC signing authenticates service-to-service REST API calls without
passwords. Each request carries a signature computed from the request contents
using a shared secret. The server recomputes the signature and rejects requests
that don't match.

This is different from JWT: there is no token, no claims structure, no base64url
payload. The signature covers the entire HTTP request, not a token string.

## Canonical Request Format

To sign a request consistently, both parties must agree on a canonical string:

```
{METHOD}\n{path}\n{timestamp}\n{body_hash}
```

Example for `POST /api/data` with body `{"key":"value"}`:

```
POST
/api/data
1704067200
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

```python
import hashlib
import hmac
import time


def canonical_request(method: str, path: str, body: bytes, timestamp: int) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{body_hash}"
```

## Signing a Request

```python
def sign_request(
    api_key: str,
    api_secret: str,
    method: str,
    path: str,
    body: bytes = b'',
) -> dict:
    """
    Sign an API request and return headers to attach.

    Returns:
        dict with 'X-API-Key', 'X-Timestamp', and 'X-Signature' headers.
    """
    timestamp = int(time.time())
    canonical = canonical_request(method, path, body, timestamp)

    sig_bytes = hmac.new(
        api_secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).digest()
    signature = sig_bytes.hex()  # hex digest, NOT base64url

    return {
        'X-API-Key': api_key,
        'X-Timestamp': str(timestamp),
        'X-Signature': signature,
    }
```

Note: API request signatures typically use **hex encoding**, not base64url,
because HTTP headers work better with hex strings.

## Verifying on the Server

```python
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
    Verify a signed API request. Returns True if valid.

    Checks:
    1. Timestamp is within max_age_seconds (replay protection)
    2. Signature matches recomputed value (timing-safe)
    """
    # 1. Replay protection
    now = int(time.time())
    if abs(now - timestamp) > max_age_seconds:
        return False

    # 2. Recompute and compare
    canonical = canonical_request(method, path, body, timestamp)
    sig_bytes = hmac.new(
        api_secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).digest()
    expected_sig = sig_bytes.hex()

    return hmac.compare_digest(expected_sig, provided_sig)
```

## Differences from JWT Signing

| Aspect | API Key HMAC | JWT HS256 |
|--------|-------------|-----------|
| What's signed | Method + path + timestamp + body | header.payload |
| Encoding | Hex digest | Base64url, no padding |
| Replay protection | Timestamp in signed message | `exp` claim |
| Claims | None — no payload structure | Structured JSON claims |
| Statefulness | Stateless | Stateless |

## Scripts

See `scripts/api_signing.py` for a complete implementation and
`scripts/test_api_signing.py` for unit tests.

## Relationship to JWT Claim Validation

API key HMAC signing and JWT HS256 validation both use HMAC-SHA256 and both require timing-safe comparison via `hmac.compare_digest`, but they protect different things.

In JWT validation (JWTValidator), the HMAC covers `base64url(header).base64url(payload)` and the result is base64url-encoded (no padding). The validator then checks claims in strict order: signature → exp (with clock skew tolerance) → nbf → iss → aud → sub, raising a specific ValueError for each failure ("invalid signature", "token expired", "invalid issuer", "invalid audience", "invalid subject").

In API key signing, HMAC covers the canonical request (method + path + timestamp + body hash) and the result is hex-encoded. There are no exp/nbf/iss/aud/sub claims — replay protection is handled by the timestamp check instead.

Both require `hmac.compare_digest` for the comparison step — never `==` — to prevent timing-oracle attacks. The base64url encoding difference (JWT uses URL-safe base64 without padding; API signing uses hex) is a common source of confusion when switching between the two authentication patterns.

## Quick Reference: API Key Signing vs JWT Claim Validation

```python
import json, base64, hmac, hashlib, time

# -- JWT validation: decode header + payload, validate claims -────────────
def _b64url_decode(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def validate_jwt(token: str, secret: str, issuer: str, audience: str) -> dict:
    """Validate a JWT. Claims: exp, nbf, iss, aud, sub."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    # Signature covers base64url(header).base64url(payload)
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()

    # Timing-safe comparison via hmac.compare_digest (shared with API signing)
    if not hmac.compare_digest(expected_sig, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_decode(parts[1]))  # base64url decode the payload
    now = int(time.time())

    # Strict claim validation order
    if payload.get('exp', now) + 5 < now:    # exp: 5-second clock skew tolerance
        raise ValueError("token expired")
    if payload.get('nbf', now) - 5 > now:    # nbf: not-before with 5s skew
        raise ValueError("token not yet valid")
    if payload.get('iss') != issuer:          # iss: issuer claim
        raise ValueError("invalid issuer")
    if payload.get('aud') != audience:        # aud: audience claim
        raise ValueError("invalid audience")

    sub = payload.get('sub', '')              # sub: subject — required, no null bytes
    if not sub or not isinstance(sub, str) or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload

# Key differences vs API key signing:
# JWT: signs base64url(header).base64url(payload); encodes result as base64url (no padding)
# API key: signs canonical_request (method+path+timestamp+body_hash); encodes as hex
# JWT: validates structured claims (exp, nbf, iss, aud, sub) from decoded payload
# API key: validates timestamp freshness only — no payload claims structure
# Both: use hmac.compare_digest for timing-safe comparison
```

JWT claim validation decodes the base64url header and payload, compares the HMAC signature with `hmac.compare_digest` (same timing-safe requirement as API key signing), then checks `exp` (with 5-second clock skew), `nbf`, `iss`, `aud`, and `sub` claims in strict order. Unlike API key signing, JWT validation must raise specific `ValueError` messages for each failed claim: "invalid signature", "token expired", "invalid issuer", "invalid audience", "invalid subject".
