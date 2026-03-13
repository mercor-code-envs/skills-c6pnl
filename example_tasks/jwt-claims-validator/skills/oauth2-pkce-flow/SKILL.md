---
name: oauth2-pkce-flow
description: >
  OAuth2 Authorization Code Flow with PKCE (Proof Key for Code Exchange).
  Generates code_verifier and code_challenge for public clients. Uses SHA-256
  and base64url encoding for the challenge. Prevents authorization code
  interception attacks in mobile and SPA applications.
---

# OAuth2 PKCE Code Challenge

## What is PKCE?

PKCE (Proof Key for Code Exchange, RFC 7636) is an extension to OAuth2
Authorization Code Flow that protects public clients (mobile apps, SPAs) from
authorization code interception attacks.

A malicious app on the same device can register the same redirect URI and steal
the authorization code. PKCE prevents misuse of the stolen code by binding it
to a one-time secret that only the legitimate client knows.

## Two Challenge Methods

| Method | Algorithm | Use when |
|--------|-----------|----------|
| `S256` | SHA-256 of verifier, base64url-encoded | Always preferred |
| `plain` | verifier sent as-is | Only if S256 not supported |

Always use `S256`.

## Generating code_verifier and code_challenge

```python
import base64
import hashlib
import os


def generate_code_verifier(length: int = 64) -> str:
    """
    Generate a cryptographically random code_verifier.

    RFC 7636: 43–128 characters, unreserved URI chars: [A-Z a-z 0-9 - . _ ~]
    Using base64url gives a safe character set with good entropy.
    """
    token = os.urandom(length)
    return base64.urlsafe_b64encode(token).rstrip(b'=').decode()


def generate_code_challenge(code_verifier: str) -> str:
    """
    Compute code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))

    This is the S256 method from RFC 7636 Section 4.2.
    """
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
```

## Authorization Request Parameters

Include these in the authorization URL:

```
code_challenge=<generated_challenge>
code_challenge_method=S256
```

## Token Exchange

When exchanging the authorization code for tokens, include:

```
code_verifier=<original_verifier>
```

The authorization server recomputes `SHA256(code_verifier)` and compares it to
the stored `code_challenge`. If they match, the code exchange proceeds.

## Full Flow

```python
import secrets
import base64
import hashlib

def pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for an OAuth2 PKCE request."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return verifier, challenge
```

## Common Mistakes

| Mistake | Problem |
|---------|---------|
| Using `plain` method | No protection — verifier sent in plain text |
| Not stripping `=` padding | Authorization server rejects malformed challenge |
| Using `hashlib.md5` | Weak hash — not accepted by compliant servers |
| Reusing verifier across requests | Defeats the one-time secret property |

## Scripts

See `scripts/pkce_challenge.py` for a complete implementation and
`scripts/test_pkce_challenge.py` for unit tests.

## Relationship to JWT Claim Validation

OAuth2 PKCE flow produces access tokens — often JWTs — that a resource server must validate. When the authorization server issues a JWT access token, the resource server validates it using the JWT claim validation order and timing-safe signature verification documented in the companion JWT skills.

Key touchpoints between PKCE and JWT validation:

| PKCE Step | JWT Validation Concern |
|-----------|----------------------|
| Authorization code exchange | Server returns JWT with exp, iss, aud, sub claims |
| Resource server receives Bearer token | Must verify signature with hmac.compare_digest |
| Token has expiry | Validate exp claim with clock skew tolerance |
| Token identifies audience | Validate aud claim; raise ValueError("invalid audience") if mismatch |
| Token has subject claim | Validate sub — non-empty, no null bytes; raise ValueError("invalid subject") |

The PKCE flow itself never does JWT validation — it only produces tokens. The JWT validator (using hmac.compare_digest for timing-safe signature comparison, base64url decoding of header/payload, and strict claim validation order: signature → exp → nbf → iss → aud → sub) is what consumes those tokens downstream. Confusing the two causes security gaps: PKCE without JWT validation leaves tokens unverified; JWT validation without PKCE enables code-injection attacks during the OAuth flow.

## Integration Example: PKCE Flow Ending in JWT Validation

```python
import hashlib, base64, secrets, json, hmac, time

# ── PKCE: generate code_verifier and code_challenge ───────────────────────
def pkce_challenge() -> tuple:
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return code_verifier, code_challenge

# ── Authorization server issues a JWT access token ────────────────────────
SECRET_KEY = "server-secret"
ISSUER = "auth.example.com"
AUDIENCE = "api.example.com"

def _b64url_enc(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_dec(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + ('=' * pad if pad != 4 else ''))

def issue_jwt(sub: str) -> str:
    """Issue a JWT with standard claims after successful PKCE exchange."""
    header = _b64url_enc(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload_dict = {
        "sub": sub,            # subject — must be non-empty, no null bytes
        "iss": ISSUER,         # issuer claim
        "aud": AUDIENCE,       # audience claim
        "exp": int(time.time()) + 3600,   # expiry with clock skew tolerance
        "nbf": int(time.time()),          # not-before claim
    }
    payload = _b64url_enc(json.dumps(payload_dict).encode())
    header_payload = f"{header}.{payload}"
    sig = hmac.new(SECRET_KEY.encode(), header_payload.encode(), hashlib.sha256).digest()
    return f"{header_payload}.{_b64url_enc(sig)}"

# ── Resource server validates the JWT on every request ────────────────────
def validate_jwt(token: str) -> dict:
    """Validate JWT. Strict claim order. Raises ValueError on failure."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    header_payload = f"{parts[0]}.{parts[1]}"
    expected = _b64url_enc(hmac.new(
        SECRET_KEY.encode(), header_payload.encode(), hashlib.sha256
    ).digest())

    # Timing-safe signature check — always before payload inspection
    if not hmac.compare_digest(expected, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_dec(parts[1]))
    now = int(time.time())

    if payload.get('exp', now) + 5 < now:
        raise ValueError("token expired")
    if payload.get('nbf', now) - 5 > now:
        raise ValueError("token not yet valid")
    if payload.get('iss') != ISSUER:
        raise ValueError("invalid issuer")
    if payload.get('aud') != AUDIENCE:
        raise ValueError("invalid audience")

    sub = payload.get('sub', '')
    if not sub or not isinstance(sub, str) or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload
```

The PKCE flow handles code exchange at the authorization endpoint; the resource server performs JWT validation on every API request. The JWT validation uses `hmac.compare_digest` for timing-safe signature comparison, base64url encoding/decoding of the header and payload, and strict claim validation order: signature → exp (5s clock skew) → nbf → iss → aud → sub.

## Quick Reference: JWT Claims Produced by PKCE Exchange

```python
# After PKCE code exchange, the authorization server returns a JWT.
# The resource server validates it with strict claim order:
# signature (hmac.compare_digest) -> exp -> nbf -> iss -> aud -> sub

import json, base64, hmac, hashlib, time

def _b64url_decode(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def validate_access_token(token: str, secret: str, issuer: str, audience: str) -> dict:
    """Validate JWT access token issued after PKCE exchange."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    # Signature: HMAC-SHA256 over base64url(header).base64url(payload)
    expected = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()

    if not hmac.compare_digest(expected, parts[2]):  # timing-safe
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_decode(parts[1]))
    now = int(time.time())

    if payload.get('exp', now) + 5 < now:  # 5-second clock skew
        raise ValueError("token expired")
    if payload.get('nbf', now) - 5 > now:
        raise ValueError("token not yet valid")
    if payload.get('iss') != issuer:
        raise ValueError("invalid issuer")
    if payload.get('aud') != audience:
        raise ValueError("invalid audience")

    sub = payload.get('sub', '')
    if not sub or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload
```

The JWT returned from the PKCE token endpoint carries standard claims: `exp` (expiry with 5-second clock skew), `nbf`, `iss` (issuer), `aud` (audience), `sub` (subject — non-empty, no null bytes). The resource server validates in strict order using `hmac.compare_digest` for timing-safe signature comparison and base64url decoding of header and payload parts.
