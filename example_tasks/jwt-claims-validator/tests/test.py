"""
Tests for TokenValidator implementation at /app/auth_validator.py.

Tests verify:
  - Correct token creation and validation (round-trip)
  - Claim validation order: signature → exp → nbf → iss → aud → sub
  - Clock skew tolerance: 5 seconds for both exp and nbf
  - Timing-safe signature comparison using hmac.compare_digest
  - Exact error messages for each failure mode
"""
import sys
import time
import json
import base64
import hmac
import hashlib
import unittest.mock
import pytest

sys.path.insert(0, '/app')
from auth_validator import TokenValidator


# ---------------------------------------------------------------------------
# Fixed test configuration
# ---------------------------------------------------------------------------

SECRET = "super-secret-key-for-testing-42"
ISSUER = "test-auth-service"
AUDIENCE = "test-api"

validator = TokenValidator(SECRET, ISSUER, AUDIENCE)


def make_valid_payload(offset_exp: int = 3600, **extra) -> dict:
    """Return a minimal valid payload with exp/iss/aud/sub."""
    now = int(time.time())
    payload = {
        "sub": "user-abc-123",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": now + offset_exp,
        "iat": now,
    }
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# Test 1: Valid token passes validation and returns correct payload
# ---------------------------------------------------------------------------

class TestValidToken:
    def test_valid_token_returns_payload(self):
        payload = make_valid_payload()
        token = validator.create_token(payload)
        result = validator.validate(token)
        assert result["sub"] == "user-abc-123"
        assert result["iss"] == ISSUER
        assert result["aud"] == AUDIENCE

    def test_valid_token_round_trip(self):
        """Test 12: create_token + validate round-trip preserves payload."""
        payload = make_valid_payload(custom_field="hello")
        token = validator.create_token(payload)
        result = validator.validate(token)
        assert result["custom_field"] == "hello"
        assert result["sub"] == payload["sub"]
        assert result["exp"] == payload["exp"]


# ---------------------------------------------------------------------------
# Test 2: Expired token raises "token expired"
# ---------------------------------------------------------------------------

class TestExpiredToken:
    def test_expired_token_raises(self):
        """exp = now - 100 is well outside 5s tolerance."""
        payload = make_valid_payload(offset_exp=-100)
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="token expired"):
            validator.validate(token)

    def test_just_expired_raises(self):
        """exp = now - 10 is outside 5s tolerance (10 > 5)."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 10
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="token expired"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Test 3: Token expiring within clock skew passes
# ---------------------------------------------------------------------------

class TestClockSkewTolerance:
    def test_exp_within_skew_passes(self):
        """exp = now - 3 is within 5s tolerance, must pass."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 3
        token = validator.create_token(payload)
        result = validator.validate(token)
        assert result["sub"] == "user-abc-123"

    def test_exp_at_boundary_passes(self):
        """exp = now - 5 is exactly at the tolerance boundary, must pass."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 5
        token = validator.create_token(payload)
        # exp + 5 >= now (exactly), should pass
        result = validator.validate(token)
        assert result is not None

    def test_nbf_within_skew_passes(self):
        """nbf = now + 3 is within 5s tolerance, must pass."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["nbf"] = now + 3
        token = validator.create_token(payload)
        result = validator.validate(token)
        assert result["sub"] == "user-abc-123"


# ---------------------------------------------------------------------------
# Test 4: Not-yet-valid token raises "token not yet valid"
# ---------------------------------------------------------------------------

class TestNotYetValidToken:
    def test_future_nbf_raises(self):
        """nbf = now + 100 is well outside 5s tolerance."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["nbf"] = now + 100
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="token not yet valid"):
            validator.validate(token)

    def test_nbf_just_outside_skew_raises(self):
        """nbf = now + 10 is outside 5s tolerance (10 > 5)."""
        now = int(time.time())
        payload = make_valid_payload()
        payload["nbf"] = now + 10
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="token not yet valid"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Test 5: Wrong issuer raises "invalid issuer"
# ---------------------------------------------------------------------------

class TestWrongIssuer:
    def test_wrong_issuer_raises(self):
        payload = make_valid_payload(iss="wrong-issuer")
        token = validator.create_token(payload)
        v2 = TokenValidator(SECRET, ISSUER, AUDIENCE)
        with pytest.raises(ValueError, match="invalid issuer"):
            v2.validate(token)

    def test_missing_issuer_raises(self):
        payload = make_valid_payload()
        del payload["iss"]
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid issuer"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Test 6: Wrong audience raises "invalid audience"
# ---------------------------------------------------------------------------

class TestWrongAudience:
    def test_wrong_audience_raises(self):
        payload = make_valid_payload(aud="wrong-audience")
        token = validator.create_token(payload)
        v2 = TokenValidator(SECRET, ISSUER, AUDIENCE)
        with pytest.raises(ValueError, match="invalid audience"):
            v2.validate(token)

    def test_missing_audience_raises(self):
        payload = make_valid_payload()
        del payload["aud"]
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid audience"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Test 7: Missing sub raises "invalid subject"
# ---------------------------------------------------------------------------

class TestInvalidSubject:
    def test_missing_sub_raises(self):
        payload = make_valid_payload()
        del payload["sub"]
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid subject"):
            validator.validate(token)

    def test_empty_sub_raises(self):
        payload = make_valid_payload()
        payload["sub"] = ""
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid subject"):
            validator.validate(token)

    def test_null_byte_in_sub_raises(self):
        payload = make_valid_payload()
        payload["sub"] = "user\x00admin"
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid subject"):
            validator.validate(token)

    def test_non_string_sub_raises(self):
        payload = make_valid_payload()
        payload["sub"] = 12345
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="invalid subject"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Test 8: Tampered signature raises "invalid signature"
# ---------------------------------------------------------------------------

class TestTamperedSignature:
    def test_tampered_sig_raises(self):
        payload = make_valid_payload()
        token = validator.create_token(payload)
        parts = token.split('.')
        # Flip the last character of the signature
        bad_sig = parts[2][:-1] + ('A' if parts[2][-1] != 'A' else 'B')
        bad_token = f"{parts[0]}.{parts[1]}.{bad_sig}"
        with pytest.raises(ValueError, match="invalid signature"):
            validator.validate(bad_token)

    def test_zeroed_sig_raises(self):
        payload = make_valid_payload()
        token = validator.create_token(payload)
        parts = token.split('.')
        bad_token = f"{parts[0]}.{parts[1]}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        with pytest.raises(ValueError, match="invalid signature"):
            validator.validate(bad_token)


# ---------------------------------------------------------------------------
# Test 9: Invalid format (not 3 parts) raises "invalid token format"
# ---------------------------------------------------------------------------

class TestInvalidFormat:
    def test_two_parts_raises(self):
        with pytest.raises(ValueError, match="invalid token format"):
            validator.validate("header.payload")

    def test_one_part_raises(self):
        with pytest.raises(ValueError, match="invalid token format"):
            validator.validate("justonepart")

    def test_four_parts_raises(self):
        with pytest.raises(ValueError, match="invalid token format"):
            validator.validate("a.b.c.d")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="invalid token format"):
            validator.validate("")


# ---------------------------------------------------------------------------
# Test 10: hmac.compare_digest is called for signature verification
# ---------------------------------------------------------------------------

class TestTimingSafeComparison:
    def test_hmac_compare_digest_is_called(self):
        """Verify that hmac.compare_digest is used (not ==) for signature comparison."""
        payload = make_valid_payload()
        token = validator.create_token(payload)

        import auth_validator as auth_mod
        with unittest.mock.patch.object(
            auth_mod.hmac, 'compare_digest', wraps=hmac.compare_digest
        ) as mock_cd:
            validator.validate(token)
            mock_cd.assert_called_once()

    def test_hmac_compare_digest_called_on_invalid_sig(self):
        """compare_digest must also be called when signature is wrong (no short-circuit)."""
        payload = make_valid_payload()
        token = validator.create_token(payload)
        parts = token.split('.')
        bad_token = f"{parts[0]}.{parts[1]}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        import auth_validator as auth_mod
        with unittest.mock.patch.object(
            auth_mod.hmac, 'compare_digest', wraps=hmac.compare_digest
        ) as mock_cd:
            with pytest.raises(ValueError, match="invalid signature"):
                validator.validate(bad_token)
            mock_cd.assert_called_once()


# ---------------------------------------------------------------------------
# Test 11: Validation order — tampered + expired raises "invalid signature"
# ---------------------------------------------------------------------------

class TestValidationOrder:
    def test_tampered_and_expired_raises_invalid_signature(self):
        """
        A token that is BOTH tampered AND expired must raise "invalid signature",
        not "token expired". Signature check MUST happen before exp check.
        """
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 1000  # definitely expired
        token = validator.create_token(payload)

        # Tamper the signature
        parts = token.split('.')
        bad_sig = parts[2][:-1] + ('A' if parts[2][-1] != 'A' else 'B')
        bad_token = f"{parts[0]}.{parts[1]}.{bad_sig}"

        with pytest.raises(ValueError, match="invalid signature"):
            validator.validate(bad_token)

    def test_exp_checked_before_iss(self):
        """
        A token that is BOTH expired AND has wrong issuer must raise "token expired",
        not "invalid issuer". exp check MUST happen before iss check.
        """
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 100
        payload["iss"] = "wrong-issuer"
        token = validator.create_token(payload)
        # Re-sign with correct secret but wrong iss still in payload
        v2 = TokenValidator(SECRET, ISSUER, AUDIENCE)
        with pytest.raises(ValueError, match="token expired"):
            v2.validate(token)

    def test_iss_checked_before_aud(self):
        """
        A token with wrong issuer AND wrong audience raises "invalid issuer", not "invalid audience".
        iss check MUST happen before aud check.
        """
        payload = make_valid_payload()
        payload["iss"] = "wrong-issuer"
        payload["aud"] = "wrong-audience"
        token = validator.create_token(payload)
        v2 = TokenValidator(SECRET, ISSUER, AUDIENCE)
        with pytest.raises(ValueError, match="invalid issuer"):
            v2.validate(token)

    def test_aud_checked_before_sub(self):
        """
        A token with wrong audience AND missing sub raises "invalid audience", not "invalid subject".
        aud check MUST happen before sub check.
        """
        payload = make_valid_payload()
        payload["aud"] = "wrong-audience"
        del payload["sub"]
        token = validator.create_token(payload)
        v2 = TokenValidator(SECRET, ISSUER, AUDIENCE)
        with pytest.raises(ValueError, match="invalid audience"):
            v2.validate(token)

    def test_nbf_checked_after_exp(self):
        """
        A token that is BOTH expired AND not-yet-valid raises "token expired".
        exp check MUST happen before nbf check.
        """
        now = int(time.time())
        payload = make_valid_payload()
        payload["exp"] = now - 100   # expired
        payload["nbf"] = now + 100   # not yet valid
        token = validator.create_token(payload)
        with pytest.raises(ValueError, match="token expired"):
            validator.validate(token)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-rA"])
    print("pass" if exit_code == 0 else "fail")
    sys.exit(exit_code)
