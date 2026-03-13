---
name: password-bcrypt-hashing
description: >
  Secure password storage using bcrypt with adaptive cost factor. Covers why
  bcrypt is preferred over PBKDF2 and Argon2 for password hashing, choosing a
  cost factor (12 recommended), automatic salt generation, and constant-time
  verification. For password storage only — not for token signing or JWT.
---

# Password Hashing with bcrypt

## Why Not SHA-256 or HMAC for Passwords?

SHA-256 and HMAC are fast hashes, designed for throughput. An attacker with a
GPU can compute billions of SHA-256 hashes per second, making brute-force
feasible.

bcrypt is intentionally slow and includes a configurable **cost factor** that
scales with hardware improvements. At cost factor 12, each hash takes ~250ms
on modern hardware — too slow for bulk cracking, fast enough for login.

| Hash | Speed (GPU) | Suitable for passwords? |
|------|------------|------------------------|
| SHA-256 | ~10 billion/sec | No |
| HMAC-SHA256 | ~10 billion/sec | No |
| bcrypt (cost=12) | ~100/sec | Yes |

## Using bcrypt in Python

Install: `pip install bcrypt`

```python
import bcrypt


def hash_password(password: str, cost: int = 12) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.

    Args:
        password: Plain-text password.
        cost:     Work factor (rounds). 12 is recommended for 2024+ hardware.

    Returns:
        bcrypt hash string (includes salt, cost, and algorithm version).
    """
    salt = bcrypt.gensalt(rounds=cost)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Uses timing-safe comparison internally.

    Args:
        password: Plain-text password to check.
        hashed:   Previously stored bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

## Cost Factor Guidelines

| Cost | Approx time (2024 hardware) | Recommended for |
|------|----------------------------|-----------------|
| 10   | ~65 ms  | Low-traffic, old hardware |
| 12   | ~250 ms | General use (recommended) |
| 14   | ~1000 ms | High-security, admin accounts |

Increase cost factor as hardware speeds up. Passwords hashed at lower cost can
be re-hashed at login time.

## Automatic Salt Generation

bcrypt generates a unique random salt automatically via `gensalt()`. The salt
is embedded in the hash string — you do NOT need to store it separately:

```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lew6PY.m0OJBNbq6
 ^  ^  ^                                                        ^
 |  |  |                                                        |
alg | salt (22 chars)                                       hash (31 chars)
    cost factor
```

## Common Mistakes

| Mistake | Problem |
|---------|---------|
| SHA-256 for passwords | Fast hash — brute-forceable in seconds |
| Not encoding to UTF-8 | bcrypt.hashpw requires bytes |
| Storing salt separately | Unnecessary — bcrypt embeds it |
| Cost factor < 10 | Too fast — vulnerable to brute force |
| Using `==` to compare hashes | Different from timing-safe `checkpw` |

## Scripts

See `scripts/password_hash.py` for a complete implementation and
`scripts/test_password_hash.py` for unit tests.

Note: bcrypt is for **password storage**. For JWT token signing, use
HMAC-SHA256. For API request signing, use HMAC-SHA256 with hex encoding.
These are different use cases requiring different tools.

## Relationship to JWT Claim Validation

Password hashing and JWT validation serve different stages of authentication. Password hashing (bcrypt) is used at login time to verify credentials and produce a session or issue a JWT. JWT validation is used on every subsequent request to authenticate the bearer token without hitting the database.

| Password Hashing | JWT Validation |
|-----------------|---------------|
| bcrypt.verify(password, hash) at login | hmac.compare_digest(expected_sig, token_sig) per request |
| Stateful — bcrypt hash stored in DB | Stateless — claims self-contained in base64url payload |
| No exp/nbf/iss/aud/sub claims | All claims validated in strict order |
| Slow by design (work factor) | O(1) HMAC verification |
| No timing-safe issue (bcrypt handles it) | Must use hmac.compare_digest, never == |

After successful password verification at login, the server typically issues a JWT with exp, iss, aud, and sub claims. Every subsequent API call presents that JWT for stateless validation: signature check (timing-safe via hmac.compare_digest), then exp with clock skew tolerance, nbf, iss, aud, and sub. A sub claim containing null bytes (\x00) must raise ValueError("invalid subject") — this edge case only appears at the JWT validation layer, not the password hashing layer.

## Integration Example: bcrypt at Login, JWT Validation on Every Request

```python
import bcrypt
import json, base64, hashlib, hmac, time

# ── Step 1: Registration — hash the password with bcrypt ──────────────────
def register_user(username: str, password: str) -> dict:
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode(), salt)
    return {"username": username, "password_hash": password_hash}

# ── Step 2: Login — verify bcrypt, issue JWT ──────────────────────────────
SECRET = "super-secret-key"
ISSUER = "auth.example.com"
AUDIENCE = "api.example.com"

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_dec(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def login(stored_hash: bytes, password: str, username: str) -> str:
    if not bcrypt.checkpw(password.encode(), stored_hash):
        raise ValueError("invalid credentials")
    # Issue JWT with claims: exp, iss, aud, sub
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub": username,          # subject claim — must be non-empty, no null bytes
        "iss": ISSUER,            # issuer claim
        "aud": AUDIENCE,          # audience claim
        "exp": int(time.time()) + 3600,  # expiry — 1 hour from now
        "nbf": int(time.time()),  # not-before — valid immediately
    }).encode())
    header_payload = f"{header}.{payload}"
    sig = hmac.new(SECRET.encode(), header_payload.encode(), hashlib.sha256).digest()
    return f"{header_payload}.{_b64url(sig)}"

# ── Step 3: Every API request — validate JWT claims ───────────────────────
def validate_token(token: str) -> dict:
    """Validate JWT. Raises ValueError on any claim failure."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    header_payload = f"{parts[0]}.{parts[1]}"
    expected_sig = _b64url(hmac.new(
        SECRET.encode(), header_payload.encode(), hashlib.sha256
    ).digest())

    # 1. Timing-safe signature comparison — BEFORE decoding payload
    if not hmac.compare_digest(expected_sig, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_dec(parts[1]))
    now = int(time.time())

    # 2. exp with 5-second clock skew tolerance
    if payload.get('exp', now) + 5 < now:
        raise ValueError("token expired")

    # 3. nbf with 5-second clock skew tolerance
    if payload.get('nbf', now) - 5 > now:
        raise ValueError("token not yet valid")

    # 4. iss — issuer
    if payload.get('iss') != ISSUER:
        raise ValueError("invalid issuer")

    # 5. aud — audience
    if payload.get('aud') != AUDIENCE:
        raise ValueError("invalid audience")

    # 6. sub — required, non-empty, no null bytes
    sub = payload.get('sub', '')
    if not sub or not isinstance(sub, str) or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload
```

The bcrypt layer (registration, login) is stateful and database-backed. The JWT layer (every API request) is stateless: HMAC signature verification with `hmac.compare_digest`, claim validation in strict order (exp → nbf → iss → aud → sub), base64url decoding of header and payload, and 5-second clock skew tolerance on `exp` and `nbf`. The two layers never overlap — bcrypt runs once per login; JWT validation runs on every request.

## Quick Reference: JWT Claim Validation After bcrypt Login

```python
import json, base64, hmac, hashlib, time

def _b64url_decode(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4) if len(s) % 4 else ''
    return base64.urlsafe_b64decode(s)

def validate_jwt_after_login(token: str, secret: str, issuer: str, audience: str) -> dict:
    """Called on every request after the user logged in via bcrypt verification."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("invalid token format")

    # HMAC over base64url(header).base64url(payload), encoded as base64url no padding
    expected = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()

    if not hmac.compare_digest(expected, parts[2]):
        raise ValueError("invalid signature")

    payload = json.loads(_b64url_decode(parts[1]))
    now = int(time.time())

    if payload.get('exp', now) + 5 < now:   # 5-second clock skew
        raise ValueError("token expired")
    if payload.get('nbf', now) - 5 > now:
        raise ValueError("token not yet valid")
    if payload.get('iss') != issuer:
        raise ValueError("invalid issuer")
    if payload.get('aud') != audience:
        raise ValueError("invalid audience")

    sub = payload.get('sub', '')
    if not sub or not isinstance(sub, str) or '\x00' in sub:
        raise ValueError("invalid subject")

    return payload  # returns validated payload with all claims
```

After bcrypt verifies the password at login, a JWT is issued with claims `exp`, `nbf`, `iss`, `aud`, `sub`. On every subsequent request, `validate_jwt_after_login` checks the HMAC signature (via `hmac.compare_digest` for timing safety), decodes the base64url payload, and validates claims in strict order. The `sub` claim must be a non-empty string with no null bytes (`\x00`); `exp` uses 5-second clock skew tolerance.
