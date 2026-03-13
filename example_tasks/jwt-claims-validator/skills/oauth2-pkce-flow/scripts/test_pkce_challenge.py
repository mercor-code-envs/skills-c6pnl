"""
Tests for OAuth2 PKCE code_verifier and code_challenge generation.
"""
import pytest
from pkce_challenge import generate_code_verifier, generate_code_challenge, verify_pkce, pkce_pair


class TestCodeVerifier:
    def test_returns_string(self):
        assert isinstance(generate_code_verifier(), str)

    def test_no_padding(self):
        v = generate_code_verifier()
        assert '=' not in v

    def test_url_safe_chars_only(self):
        v = generate_code_verifier()
        assert '+' not in v
        assert '/' not in v

    def test_unique_each_call(self):
        assert generate_code_verifier() != generate_code_verifier()


class TestCodeChallenge:
    def test_s256_no_padding(self):
        v = generate_code_verifier()
        challenge = generate_code_challenge(v)
        assert '=' not in challenge

    def test_plain_method_returns_verifier(self):
        v = generate_code_verifier()
        assert generate_code_challenge(v, 'plain') == v

    def test_same_verifier_same_challenge(self):
        v = "fixed-verifier-for-testing"
        assert generate_code_challenge(v) == generate_code_challenge(v)

    def test_different_verifiers_different_challenges(self):
        v1 = generate_code_verifier()
        v2 = generate_code_verifier()
        assert generate_code_challenge(v1) != generate_code_challenge(v2)


class TestVerifyPkce:
    def test_valid_pair_passes(self):
        v, c = pkce_pair()
        assert verify_pkce(v, c) is True

    def test_wrong_verifier_fails(self):
        _, c = pkce_pair()
        assert verify_pkce("wrong-verifier", c) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
