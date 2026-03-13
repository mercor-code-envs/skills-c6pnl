"""
Tests for JWT claim validation order and clock skew tolerance.
"""
import time
import pytest
from jwt_validation_order import JWTValidator

SECRET = "test-secret"
ISSUER = "test-iss"
AUDIENCE = "test-aud"

v = JWTValidator(SECRET, ISSUER, AUDIENCE)


def base_payload(**overrides) -> dict:
    now = int(time.time())
    p = {"sub": "user1", "iss": ISSUER, "aud": AUDIENCE, "exp": now + 3600}
    p.update(overrides)
    return p


class TestValidationOrder:
    def test_tampered_and_expired_raises_invalid_signature(self):
        now = int(time.time())
        p = base_payload(exp=now - 1000)
        token = v.create_token(p)
        parts = token.split('.')
        bad = f"{parts[0]}.{parts[1]}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        with pytest.raises(ValueError, match="invalid signature"):
            v.validate(bad)

    def test_expired_and_wrong_iss_raises_token_expired(self):
        now = int(time.time())
        p = base_payload(exp=now - 100, iss="wrong")
        token = v.create_token(p)
        with pytest.raises(ValueError, match="token expired"):
            v.validate(token)

    def test_wrong_iss_and_wrong_aud_raises_invalid_issuer(self):
        p = base_payload(iss="wrong", aud="wrong")
        token = v.create_token(p)
        with pytest.raises(ValueError, match="invalid issuer"):
            v.validate(token)


class TestClockSkew:
    def test_exp_minus_3_passes(self):
        now = int(time.time())
        p = base_payload(exp=now - 3)
        token = v.create_token(p)
        result = v.validate(token)
        assert result["sub"] == "user1"

    def test_exp_minus_10_fails(self):
        now = int(time.time())
        p = base_payload(exp=now - 10)
        token = v.create_token(p)
        with pytest.raises(ValueError, match="token expired"):
            v.validate(token)

    def test_nbf_plus_3_passes(self):
        now = int(time.time())
        p = base_payload(nbf=now + 3)
        token = v.create_token(p)
        result = v.validate(token)
        assert result["sub"] == "user1"

    def test_nbf_plus_10_fails(self):
        now = int(time.time())
        p = base_payload(nbf=now + 10)
        token = v.create_token(p)
        with pytest.raises(ValueError, match="token not yet valid"):
            v.validate(token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
