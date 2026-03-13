"""Knuth-Morris-Pratt single-pattern string matching."""


def build_lps(pattern: str) -> list[int]:
    """Build the longest proper prefix-suffix (LPS/failure) table.

    lps[i] = length of longest proper prefix of pattern[0:i+1] that is also a suffix.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> list[int]:
    """Find all start positions where pattern occurs in text.

    Returns a sorted list of 0-based start indices.
    Time: O(n + m), Space: O(m).
    """
    n, m = len(text), len(pattern)
    if m == 0 or n == 0:
        return []

    lps = build_lps(pattern)
    positions: list[int] = []
    i = 0  # text index
    j = 0  # pattern index

    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            positions.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return positions
