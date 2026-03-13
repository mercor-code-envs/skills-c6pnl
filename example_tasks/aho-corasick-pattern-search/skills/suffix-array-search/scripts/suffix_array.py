"""Suffix array construction and binary-search pattern lookup."""
import bisect


def build_suffix_array(text: str) -> list[int]:
    """Build the suffix array for text in O(n^2 log n) via Python sort.

    Returns list of suffix start indices sorted lexicographically by their suffixes.
    """
    return sorted(range(len(text)), key=lambda i: text[i:])


def build_lcp(text: str, sa: list[int]) -> list[int]:
    """Build the LCP (longest common prefix) array using Kasai's algorithm in O(n)."""
    n = len(text)
    rank = [0] * n
    for i, s in enumerate(sa):
        rank[s] = i

    lcp = [0] * n
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1
    return lcp


def search_pattern(text: str, sa: list[int], pattern: str) -> list[int]:
    """Find all start positions of pattern in text using binary search on the suffix array.

    Returns a sorted list of 0-based start positions.
    Time: O(m log n) after suffix array is built.
    """
    m = len(pattern)
    if m == 0:
        return []

    lo = bisect.bisect_left(sa, pattern, key=lambda i: text[i : i + m])
    hi = bisect.bisect_right(sa, pattern, key=lambda i: text[i : i + m])

    return sorted(sa[lo:hi])
