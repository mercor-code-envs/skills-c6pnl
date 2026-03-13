"""
Tests for API key HMAC request signing.
"""
import time
import pytest
from api_signing import sign_request, verify_request, canonical_request


SECRET = "api-test-secret"
API_KEY = "test-key-abc"


class TestCanonicalRequest:
    def test_format(self):
        c = canonical_request("GET", "/api/v1/data", b"", 1704067200)
        parts = c.split('\n')
        assert parts[0] == "GET"
        assert parts[1] == "/api/v1/data"
        assert parts[2] == "1704067200"
        assert len(parts[3]) == 64  # sha256 hex

    def test_method_uppercased(self):
        c = canonical_request("post", "/path", b"", 0)
        assert c.startswith("POST\n")

    def test_body_hash_changes_with_body(self):
        c1 = canonical_request("POST", "/", b"body1", 0)
        c2 = canonical_request("POST", "/", b"body2", 0)
        assert c1 != c2


class TestSignAndVerify:
    def test_valid_signature_verifies(self):
        headers = sign_request(API_KEY, SECRET, "GET", "/test")
        ts = int(headers['X-Timestamp'])
        assert verify_request(SECRET, "GET", "/test", b'', ts, headers['X-Signature'])

    def test_wrong_secret_fails(self):
        headers = sign_request(API_KEY, SECRET, "GET", "/test")
        ts = int(headers['X-Timestamp'])
        assert not verify_request("wrong-secret", "GET", "/test", b'', ts, headers['X-Signature'])

    def test_tampered_body_fails(self):
        headers = sign_request(API_KEY, SECRET, "POST", "/data", b'original')
        ts = int(headers['X-Timestamp'])
        assert not verify_request(SECRET, "POST", "/data", b'tampered', ts, headers['X-Signature'])

    def test_old_timestamp_fails(self):
        ts = int(time.time()) - 400  # older than 300s max_age
        canonical = canonical_request("GET", "/", b"", ts)
        import hmac as hmac_mod, hashlib
        sig = hmac_mod.new(SECRET.encode(), canonical.encode(), hashlib.sha256).digest().hex()
        assert not verify_request(SECRET, "GET", "/", b'', ts, sig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
