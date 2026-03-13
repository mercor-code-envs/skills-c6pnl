"""
Secure password hashing and verification using bcrypt.

Requires: pip install bcrypt
"""


def hash_password(password: str, cost: int = 12) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.

    Args:
        password: Plain-text password string.
        cost:     bcrypt work factor (rounds). Default 12.

    Returns:
        bcrypt hash string (includes algorithm, cost, salt, and hash).
    """
    try:
        import bcrypt
    except ImportError:
        raise ImportError("bcrypt is required: pip install bcrypt")
    salt = bcrypt.gensalt(rounds=cost)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Uses timing-safe comparison internally via bcrypt.checkpw.

    Args:
        password: Plain-text password to verify.
        hashed:   Previously stored hash string from hash_password().

    Returns:
        True if password matches, False otherwise.
    """
    try:
        import bcrypt
    except ImportError:
        raise ImportError("bcrypt is required: pip install bcrypt")
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def needs_rehash(hashed: str, desired_cost: int = 12) -> bool:
    """
    Check if a stored hash was made with a lower cost factor.

    Use at login time to upgrade old hashes transparently.
    """
    try:
        import bcrypt
        return bcrypt.checkpw(b'', hashed.encode('utf-8')) is not None
    except Exception:
        pass
    # Parse cost from hash string: $2b$12$...
    parts = hashed.split('$')
    if len(parts) >= 3:
        try:
            current_cost = int(parts[2])
            return current_cost < desired_cost
        except ValueError:
            pass
    return True
