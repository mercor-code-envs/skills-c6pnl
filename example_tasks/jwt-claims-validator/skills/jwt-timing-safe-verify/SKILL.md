---
name: jwt-timing-safe-verify
description: >
  HMAC-SHA256 signing for JWT tokens with base64url encoding (no padding) and
  timing-safe comparison using hmac.compare_digest. Explains why string == leaks
  timing information and how compare_digest prevents signature oracle attacks.
---

# JWT Timing-Safe Signature Verification

## Why String == Is Dangerous

A naive signature check like `expected == provided` compares strings byte by
byte and returns as soon as a mismatch is found. This creates a
**timing oracle**: an attacker can forge a signature one byte at a time by
measuring response times. With enough queries the full valid signature can be
reconstructed without knowing the secret.

```python
# WRONG — leaks timing information
if expected_sig == parts[2]:
    ...

# CORRECT — constant time regardless of how many bytes match
if hmac.compare_digest(expected_sig, parts[2]):
    ...
```

`hmac.compare_digest` is specifically designed for this: it always compares
all bytes and returns in constant time.

## HMAC-SHA256 Signature Computation

```python
import hashlib
import hmac

def _sign(secret: str, header_payload: str) -> str:
    """
    Compute HMAC-SHA256 over 'header.payload' and return as base64url (no padding).
    """
    sig_bytes = hmac.new(
        secret.encode(),          # key as bytes
        header_payload.encode(),  # message as bytes
        hashlib.sha256            # digest algorithm
    ).digest()                    # returns raw 32-byte digest
    return _b64url_encode(sig_bytes)
```

The message signed is the string `"{b64url_header}.{b64url_payload}"` — the
first two dot-separated parts of the token joined by a literal dot.

## Base64url Encoding and Decoding (No Padding)

Standard JWT tokens use base64url WITHOUT trailing `=` padding.

```python
import base64

def _b64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string, stripping '=' padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _b64url_decode(s: str) -> bytes:
    """Decode a base64url string, adding back padding as needed."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)
```

Key details:
- `urlsafe_b64encode` uses `-` and `_` instead of `+` and `/`
- `.rstrip(b'=')` removes the `=` padding characters
- Decoding requires restoring the padding before calling `urlsafe_b64decode`
- `padding != 4` guard avoids adding 4 extra `=` when the string is already
  a multiple of 4 characters long

## Full Token Structure

```
{base64url(header)}.{base64url(payload)}.{base64url(HMAC-SHA256(header.payload))}
```

Example header: `{"alg": "HS256", "typ": "JWT"}`

```python
def create_token(secret: str, issuer: str, payload: dict) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body   = _b64url_encode(json.dumps(payload).encode())
    header_payload = f"{header}.{body}"
    sig = _sign(secret, header_payload)
    return f"{header_payload}.{sig}"
```

## Why Signature Check Comes Before Payload Parsing

1. **Security**: Parsing untrusted base64/JSON before verifying authenticity
   can expose JSON parsing vulnerabilities.
2. **Correctness**: Claim checks (exp, iss, etc.) are only meaningful if the
   token is genuine.
3. **Error semantics**: A test that sends a tampered+expired token must see
   "invalid signature", not "token expired".

## Common Mistakes

| Mistake | Problem |
|---------|---------|
| `expected == parts[2]` | Timing oracle; fails `compare_digest` call assertion tests |
| `base64.b64encode` instead of `urlsafe_b64encode` | Uses `+`/`/` — breaks URL-safe encoding |
| Not stripping `=` padding | Signature string has trailing `=`, won't match tokens from standard libraries |
| `hashlib.sha256(msg).digest()` | Plain hash — NOT an HMAC; ignores the secret key entirely |
| Parsing payload before signature check | Wrong error raised for tampered tokens; potential JSON injection |

## Scripts

See `scripts/jwt_signing.py` for a complete working implementation and
`scripts/test_jwt_signing.py` for unit tests covering signing, verification,
and timing-safe behavior.
