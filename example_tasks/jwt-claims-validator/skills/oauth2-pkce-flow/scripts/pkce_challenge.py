"""
OAuth2 PKCE code_verifier and code_challenge generation (RFC 7636).
"""
import base64
import hashlib
import os
import secrets


def generate_code_verifier(length: int = 32) -> str:
    """Generate a cryptographically random PKCE code_verifier."""
    token = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(token).rstrip(b'=').decode()


def generate_code_challenge(code_verifier: str, method: str = 'S256') -> str:
    """
    Compute the PKCE code_challenge.

    Args:
        code_verifier: The plain-text verifier string.
        method:        'S256' (default) or 'plain'.

    Returns:
        code_challenge string.
    """
    if method == 'S256':
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    elif method == 'plain':
        return code_verifier
    else:
        raise ValueError(f"Unsupported PKCE method: {method}")


def verify_pkce(code_verifier: str, code_challenge: str, method: str = 'S256') -> bool:
    """
    Verify a PKCE code_verifier against a stored code_challenge.

    Used by the authorization server during token exchange.
    """
    expected = generate_code_challenge(code_verifier, method)
    return expected == code_challenge


def pkce_pair() -> tuple:
    """Return (code_verifier, code_challenge) for a new OAuth2 PKCE request."""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    return verifier, challenge
