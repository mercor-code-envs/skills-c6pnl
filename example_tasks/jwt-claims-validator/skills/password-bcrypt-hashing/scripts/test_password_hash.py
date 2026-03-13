"""
Tests for bcrypt password hashing and verification.

Note: bcrypt is required (pip install bcrypt).
If bcrypt is not available, tests are skipped.
"""
import pytest

bcrypt_available = True
try:
    import bcrypt
except ImportError:
    bcrypt_available = False

pytestmark = pytest.mark.skipif(not bcrypt_available, reason="bcrypt not installed")

from password_hash import hash_password, verify_password


class TestHashPassword:
    def test_returns_string(self):
        h = hash_password("mypassword", cost=4)
        assert isinstance(h, str)

    def test_starts_with_bcrypt_prefix(self):
        h = hash_password("test", cost=4)
        assert h.startswith("$2b$")

    def test_cost_factor_embedded(self):
        h = hash_password("test", cost=4)
        assert "$04$" in h

    def test_unique_hashes(self):
        h1 = hash_password("same-password", cost=4)
        h2 = hash_password("same-password", cost=4)
        assert h1 != h2  # different salts


class TestVerifyPassword:
    def test_correct_password_passes(self):
        h = hash_password("correct-horse", cost=4)
        assert verify_password("correct-horse", h) is True

    def test_wrong_password_fails(self):
        h = hash_password("correct-horse", cost=4)
        assert verify_password("wrong-password", h) is False

    def test_empty_password_fails(self):
        h = hash_password("nonempty", cost=4)
        assert verify_password("", h) is False

    def test_case_sensitive(self):
        h = hash_password("Password", cost=4)
        assert verify_password("password", h) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
