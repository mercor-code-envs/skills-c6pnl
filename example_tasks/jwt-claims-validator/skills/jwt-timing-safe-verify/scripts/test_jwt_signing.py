"""
Tests for JWT signing and timing-safe verification.
"""
import unittest.mock
import hmac as hmac_module
import pytest
from jwt_signing import create_token, verify_signature, sign, _b64url_encode, _b64url_decode

SECRET = "my-test-secret"


class TestBase64Url:
    def test_encode_decode_roundtrip(self):
        data = b"hello world 123"
        assert _b64url_decode(_b64url_encode(data)) == data

    def test_no_padding_in_encoded(self):
        # Should never have trailing '=' characters
        for length in range(1, 20):
            encoded = _b64url_encode(b'x' * length)
            assert '=' not in encoded

    def test_uses_url_safe_chars(self):
        # urlsafe encoding must not contain + or /
        for i in range(256):
            encoded = _b64url_encode(bytes([i] * 3))
            assert '+' not in encoded
            assert '/' not in encoded


class TestSigning:
    def test_sign_returns_string(self):
        sig = sign(SECRET, "header.payload")
        assert isinstance(sig, str)

    def test_sign_no_padding(self):
        sig = sign(SECRET, "header.payload")
        assert '=' not in sig

    def test_same_input_same_signature(self):
        sig1 = sign(SECRET, "a.b")
        sig2 = sign(SECRET, "a.b")
        assert sig1 == sig2

    def test_different_secret_different_signature(self):
        sig1 = sign("secret1", "a.b")
        sig2 = sign("secret2", "a.b")
        assert sig1 != sig2


class TestCreateVerify:
    def test_roundtrip(self):
        payload = {"sub": "user1", "iss": "myapp"}
        token = create_token(SECRET, payload)
        result = verify_signature(token, SECRET)
        assert result["sub"] == "user1"

    def test_token_has_three_parts(self):
        token = create_token(SECRET, {"sub": "x"})
        assert len(token.split('.')) == 3

    def test_wrong_secret_raises(self):
        token = create_token(SECRET, {"sub": "x"})
        with pytest.raises(ValueError, match="invalid signature"):
            verify_signature(token, "wrong-secret")

    def test_tampered_payload_raises(self):
        token = create_token(SECRET, {"sub": "x"})
        parts = token.split('.')
        # Replace payload with something different
        bad_token = f"{parts[0]}.AAAAAAA.{parts[2]}"
        with pytest.raises(ValueError, match="invalid signature"):
            verify_signature(bad_token, SECRET)


class TestTimingSafe:
    def test_compare_digest_is_called(self):
        payload = {"sub": "user1"}
        token = create_token(SECRET, payload)
        import jwt_signing as mod
        with unittest.mock.patch.object(
            mod.hmac, 'compare_digest', wraps=hmac_module.compare_digest
        ) as mock_cd:
            verify_signature(token, SECRET)
            mock_cd.assert_called_once()

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="invalid token format"):
            verify_signature("only.two", SECRET)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
