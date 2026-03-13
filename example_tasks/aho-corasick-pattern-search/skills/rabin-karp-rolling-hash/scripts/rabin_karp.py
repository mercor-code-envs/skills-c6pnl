"""Rabin-Karp rolling hash string search (single pattern)."""

BASE = 256
MOD = 10**9 + 7


def rabin_karp(text: str, pattern: str) -> list[int]:
    """Find all start positions of pattern in text using rolling hash.

    Returns a sorted list of 0-based start indices.
    Average O(n + m) time, O(1) extra space.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    # BASE^(m-1) mod MOD — used to remove the contribution of the leftmost character
    h = pow(BASE, m - 1, MOD)

    # Compute initial hashes for pattern and first window of text
    p_hash = 0
    t_hash = 0
    for i in range(m):
        p_hash = (p_hash * BASE + ord(pattern[i])) % MOD
        t_hash = (t_hash * BASE + ord(text[i])) % MOD

    positions: list[int] = []
    for i in range(n - m + 1):
        if p_hash == t_hash:
            # Verify to rule out hash collisions
            if text[i : i + m] == pattern:
                positions.append(i)
        if i < n - m:
            t_hash = (BASE * (t_hash - ord(text[i]) * h) + ord(text[i + m])) % MOD

    return positions
