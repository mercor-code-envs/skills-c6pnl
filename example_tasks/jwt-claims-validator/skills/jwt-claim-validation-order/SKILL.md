---
name: jwt-claim-validation-order
description: >
  Exact validation sequence for JWT claims: signature → exp → nbf → iss → aud →
  sub → custom. Includes 5-second clock skew tolerance for exp and nbf. Explains
  why order matters for security and correctness.
---

# JWT Claim Validation Order

## Why Order Matters

JWT validation has a strict required order. Checking claims in the wrong order
can cause two classes of bugs:

1. **Wrong error message exposed**: If `iss` is checked before `exp`, a
   tampered-and-expired token raises "invalid issuer" instead of "token expired",
   leaking information about the validation logic and causing test failures.

2. **Security bypass**: Validating audience or subject before confirming the
   token has not expired allows a client to use a stale token until a
   non-time claim fails.

## Canonical Validation Sequence

Always validate in this order:

```
1. token format  (3 dot-separated parts)
2. signature     (HMAC-SHA256, timing-safe)
3. exp           (expiry, with 5-second clock skew)
4. nbf           (not-before, with 5-second clock skew)
5. iss           (issuer string equality)
6. aud           (audience string equality)
7. sub           (subject: required, non-empty string, no null bytes)
8. custom claims (application-specific)
```

Stop and raise the appropriate error as soon as a check fails. Never continue
to the next check after a failure.

## Clock Skew Tolerance: 5 Seconds

Clocks on distributed systems are never perfectly synchronized. A 5-second
tolerance prevents spurious failures when the issuer and validator clocks
differ slightly.

### exp (expiry) check

```python
now = int(time.time())

if 'exp' in payload:
    # Allow 5 extra seconds beyond the expiry timestamp
    if payload['exp'] + 5 < now:
        raise ValueError("token expired")
```

The token is still valid if `exp + 5 >= now`. A token with `exp = now - 3`
passes; a token with `exp = now - 10` fails.

### nbf (not-before) check

```python
if 'nbf' in payload:
    # Allow the token to be used up to 5 seconds before nbf
    if payload['nbf'] - 5 > now:
        raise ValueError("token not yet valid")
```

The token is usable if `nbf - 5 <= now`. A token with `nbf = now + 3` passes;
a token with `nbf = now + 10` fails.

## ⚠️ TWO RULES THAT BREAK TESTS IF VIOLATED

> 1. **Use `now = int(time.time())`** — never `time.time()` (float). A float like `1741772400.001`
>    makes `exp + 5 < now` true for a boundary token where `exp = now - 5`. This breaks
>    `test_exp_at_boundary_passes`. **Always cast to int.**
>
> 2. **Check `'\x00' in sub` for null bytes** — `"user\x00admin"` passes both `bool(sub)` and
>    `isinstance(sub, str)` checks but must be rejected. Without this check,
>    `test_null_byte_in_sub_raises` fails. The full sub check is:
>    ```python
>    sub = payload.get('sub')
>    if not sub or not isinstance(sub, str) or '\x00' in sub:
>        raise ValueError("invalid subject")
>    ```

## Common Mistakes

| Mistake | Consequence |
|---------|-------------|
| Check `iss` before `exp` | Expired+wrong-issuer token raises "invalid issuer" instead of "token expired" |
| Check `aud` before `iss` | Wrong-issuer+wrong-aud token raises "invalid audience" instead of "invalid issuer" |
| Check `sub` before `aud` | Wrong-aud+missing-sub raises "invalid subject" instead of "invalid audience" |
| No clock skew on `nbf` | Tokens issued with `nbf = now + 2` are rejected by validators with clock 2s behind |
| Strict `exp > now` check | Tokens with `exp = now` are rejected (off-by-one) |
| **`now = time.time()` (float)** | **`test_exp_at_boundary_passes` fails**: a token with `exp = now - 5` should pass but sub-second float precision causes `exp + 5 < now` to be True. Use `now = int(time.time())` — always integer seconds.** |
| **No `'\x00' in sub` check** | **`test_null_byte_in_sub_raises` fails**: `"user\x00admin"` passes `not sub` and `isinstance(sub, str)` but must be rejected. Check `'\x00' in sub` explicitly.** |

## Scripts

See `scripts/jwt_validation_order.py` for a complete standalone implementation
and `scripts/test_jwt_validation_order.py` for unit tests covering all cases.
