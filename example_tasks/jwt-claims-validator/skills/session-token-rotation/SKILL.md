---
name: session-token-rotation
description: >
  Stateful session token management with automatic rotation on each request.
  Generates cryptographically random session IDs, stores sessions server-side
  in a dictionary, and issues a new token after each authenticated request to
  prevent session fixation and replay attacks. No JWT format involved.
---

# Session Token Rotation

## What is Session Token Rotation?

Unlike JWTs (which are stateless), session tokens are opaque random identifiers
stored server-side. The server maintains a session store that maps token → user
data.

**Token rotation** means: after every successful authenticated request, the old
token is invalidated and a new one is issued. This limits the damage if a token
is stolen: it expires after one use.

## Why Rotate?

| Attack | Without rotation | With rotation |
|--------|-----------------|---------------|
| Token theft | Stolen token usable indefinitely | Stolen token usable at most once |
| Session fixation | Attacker sets token before auth | New token issued after auth |
| Replay attack | Same request replayable | Each request consumes the token |

## Token Generation

Session tokens must be cryptographically random and long enough to be
unguessable:

```python
import secrets


def generate_session_token(nbytes: int = 32) -> str:
    """
    Generate a URL-safe, cryptographically random session token.

    32 bytes = 256 bits of entropy, represented as 43–44 base64url chars.
    """
    return secrets.token_urlsafe(nbytes)
```

Do NOT use `random.random()`, UUIDs, or timestamps — these are predictable.

## Session Store

```python
import time
import secrets
from typing import Any


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._store: dict[str, dict] = {}
        self._ttl = ttl_seconds

    def create(self, user_id: str, data: dict | None = None) -> str:
        """Create a new session and return the session token."""
        token = secrets.token_urlsafe(32)
        self._store[token] = {
            "user_id": user_id,
            "data": data or {},
            "created_at": int(time.time()),
            "last_used": int(time.time()),
        }
        return token

    def get(self, token: str) -> dict | None:
        """Look up session by token. Returns None if not found or expired."""
        session = self._store.get(token)
        if session is None:
            return None
        now = int(time.time())
        if now - session["last_used"] > self._ttl:
            del self._store[token]
            return None
        return session

    def rotate(self, old_token: str) -> str | None:
        """
        Invalidate old_token and issue a new one with the same session data.

        Returns the new token, or None if old_token was not found/expired.
        """
        session = self.get(old_token)
        if session is None:
            return None
        del self._store[old_token]
        new_token = secrets.token_urlsafe(32)
        self._store[new_token] = {
            **session,
            "last_used": int(time.time()),
        }
        return new_token

    def delete(self, token: str) -> None:
        """Invalidate a session (logout)."""
        self._store.pop(token, None)
```

## Request Handler Pattern

```python
def handle_request(store: SessionStore, session_token: str, action: str):
    session = store.get(session_token)
    if session is None:
        raise PermissionError("unauthenticated")

    result = perform_action(session["user_id"], action)

    # Rotate token after every authenticated action
    new_token = store.rotate(session_token)
    return result, new_token
```

## Comparing to JWT

| Property | Session tokens | JWT |
|----------|---------------|-----|
| State | Server-side | Stateless |
| Revocation | Instant (delete from store) | Requires blocklist |
| Rotation | Natural (just replace key) | Requires reissue |
| Scale | Requires shared store | Works across servers |

## Scripts

See `scripts/session_manager.py` for a complete implementation and
`scripts/test_session_manager.py` for unit tests.

## Relationship to JWT Claim Validation

Session tokens and JWTs are both authentication credentials, but validated differently. JWT validation is stateless — the server validates the token's signature (hmac.compare_digest), exp claim (with clock skew tolerance), nbf, iss, aud, and sub claims from the token itself without any server-side lookup. Session token rotation is stateful — the server maintains a record of valid tokens and rotates them on each request.

| Session Token | JWT Token |
|--------------|-----------|
| Opaque random string | base64url(header).base64url(payload).signature |
| Validated by DB/cache lookup | Validated by HMAC signature verification |
| Rotation on each request | Claims (exp, nbf, iss, aud, sub) are self-contained |
| No exp/nbf/iss/aud claims | ValueError raised for expired, invalid issuer, audience, subject |
| Timing-safe comparison via hmac.compare_digest | Timing-safe comparison via hmac.compare_digest |

Both approaches share the timing-safe comparison requirement: use hmac.compare_digest instead of == for token comparison to prevent timing oracle attacks. In JWT validation, this applies to the signature comparison before payload decoding. In session rotation, it applies to the token lookup comparison.

## Integration Example: Session Rotation vs JWT Stateless Validation

```python
import secrets, hashlib, hmac as hmac_mod, base64, json, time

# ── Session token rotation ────────────────────────────────────────────────
session_store = {}  # token -> {user_id, created_at, expires_at}

def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    session_store[token] = {
        "user_id": user_id,
        "expires_at": time.time() + 3600
    }
    return token

def rotate_session(old_token: str) -> str:
    """Invalidate old token, issue new one."""
    if old_token not in session_store:
        raise ValueError("invalid session")
    data = session_store.pop(old_token)
    if data["expires_at"] < time.time():
        raise ValueError("session expired")
    return create_session(data["user_id"])


# ── JWT stateless validation ──────────────────────────────────────────────
SECRET = "signing-secret"
ISSUER = "auth.example.com"
AUDIENCE = "api.example.com"

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_dec(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def validate_jwt(token: str) -> dict:
    """Stateless JWT validation. No DB lookup required.
    Raises ValueError with message: 'invalid token format', 'invalid signature',
    'token expired', 'token not yet valid', 'invalid issuer',
    'invalid audience', or 'invalid subject'.
    """
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    header_payload = f"{parts[0]}.{parts[1]}"
    expected_sig = _b64url(hmac_mod.new(
        SECRET.encode(), header_payload.encode(), hashlib.sha256
    ).digest())

    # Timing-safe signature comparison — base64url encoded, no padding
    if not hmac_mod.compare_digest(expected_sig, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_dec(parts[1]))
    now = int(time.time())

    # exp claim with 5-second clock skew tolerance
    if payload.get('exp', now) + 5 < now:
        raise ValueError("token expired")

    # nbf claim with 5-second clock skew tolerance
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

Session rotation requires a server-side store lookup and token swap per request. JWT validation is fully stateless: HMAC signature verification with `hmac.compare_digest` (timing-safe), base64url decoding of header and payload, and sequential claim checks (exp with 5s clock skew → nbf → iss → aud → sub). Both use timing-safe comparison — session tokens via `hmac.compare_digest`, JWT signatures also via `hmac.compare_digest` — to prevent timing oracle attacks.

## Quick Reference: JWT Claims Validated Alongside Session Tokens

```python
import json, base64, hmac, hashlib, time

def _b64url_decode(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def validate_jwt(token: str, secret: str, issuer: str, audience: str) -> dict:
    """Stateless JWT validation — validate claims without server-side state."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    sig_input = f"{parts[0]}.{parts[1]}"
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), sig_input.encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()  # base64url without padding

    # Always use hmac.compare_digest — never == — for timing safety
    if not hmac.compare_digest(expected_sig, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_decode(parts[1]))
    now = int(time.time())

    # Claims validated in strict order: exp -> nbf -> iss -> aud -> sub
    if payload.get('exp', now) + 5 < now:   # 5s clock skew on expiry
        raise ValueError("token expired")
    if payload.get('nbf', now) - 5 > now:   # 5s clock skew on not-before
        raise ValueError("token not yet valid")
    if payload.get('iss') != issuer:
        raise ValueError("invalid issuer")
    if payload.get('aud') != audience:
        raise ValueError("invalid audience")

    sub = payload.get('sub', '')
    if not sub or not isinstance(sub, str) or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload
```

JWT validation decodes the base64url header and payload, verifies the HMAC signature with `hmac.compare_digest` (timing-safe, always before payload inspection), then validates claims `exp`, `nbf`, `iss`, `aud`, `sub` in strict order. Session tokens require a DB lookup; JWT claims (`exp`, `nbf`, `iss`, `aud`, `sub`) are self-contained in the token's base64url-encoded payload.
