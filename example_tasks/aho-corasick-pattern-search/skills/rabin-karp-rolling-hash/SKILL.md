---
name: rabin-karp-rolling-hash
description: >
  Uses polynomial rolling hash (fingerprint) to find pattern occurrences in text.
  Computes a hash for the pattern and slides a same-length window over the text,
  updating the hash in O(1) per step. Best for single-pattern search or plagiarism
  detection; not designed for simultaneous multi-pattern search over a single pass.
---

# Rabin-Karp Rolling Hash Search

Rabin-Karp uses a **rolling hash** (fingerprint) to find all occurrences of a
**single pattern** in text in average O(n + m) time with O(1) extra space.

> **Note:** Rabin-Karp is built for one pattern at a time. For simultaneous
> multi-pattern search in O(n + total_m) time, the Aho-Corasick automaton is
> the standard approach.

## Rolling Hash Formula

Use a polynomial hash with a large prime modulus to minimise collisions:

```
hash(s[0..m-1]) = s[0]*BASE^(m-1) + s[1]*BASE^(m-2) + ... + s[m-1]*BASE^0  (mod MOD)
```

Sliding the window one step right:
```
hash(s[1..m]) = (hash(s[0..m-1]) - s[0]*BASE^(m-1)) * BASE + s[m]  (mod MOD)
```

## Implementation

```python
BASE = 256
MOD  = 10**9 + 7

def rabin_karp(text: str, pattern: str) -> list[int]:
    """Find all start positions of pattern in text.

    Returns list of 0-based start indices.
    Average O(n + m), worst-case O(n*m) due to hash collisions.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    # Precompute BASE^(m-1) mod MOD
    h = pow(BASE, m - 1, MOD)

    # Compute initial hashes
    p_hash = 0
    t_hash = 0
    for i in range(m):
        p_hash = (p_hash * BASE + ord(pattern[i])) % MOD
        t_hash = (t_hash * BASE + ord(text[i])) % MOD

    positions = []
    for i in range(n - m + 1):
        if p_hash == t_hash:
            # Hash match — verify character by character to avoid false positives
            if text[i:i + m] == pattern:
                positions.append(i)
        if i < n - m:
            # Roll the hash: remove leftmost char, add next char
            t_hash = (BASE * (t_hash - ord(text[i]) * h) + ord(text[i + m])) % MOD

    return positions
```

## Example

```python
positions = rabin_karp("abcabcabc", "abc")
# Returns: [0, 3, 6]
```

## Complexity

| Case | Time | Space |
|------|------|-------|
| Average | O(n + m) | O(1) |
| Worst (all hash collisions) | O(n*m) | O(1) |

## Use Cases

- Single-pattern search where simplicity matters
- Plagiarism detection (comparing many documents, one pattern at a time)
- 2D pattern matching (extension of rolling hash to 2D grids)

## Relationship to Aho-Corasick

Rabin-Karp's rolling hash provides O(1) amortised window advancement using a hash function to detect potential matches. Like Aho-Corasick, it can search for multiple patterns — but through a hash set lookup per window rather than a trie automaton traversal.

Key differences:

| Rabin-Karp | Aho-Corasick |
|-----------|-------------|
| Hash set of pattern hashes | Trie (goto table) + failure links |
| O(n*m) worst case (hash collisions) | O(n + total_pattern_length) guaranteed |
| No output function | Output function at each trie state |
| Window slides by 1 character | State transition on each character |

Aho-Corasick's trie construction (BFS over the goto table to compute failure links and output function) eliminates hash collisions entirely. The failure links allow the automaton to backtrack through the trie without re-scanning text characters, making every match deterministic — not a candidate requiring verification as in Rabin-Karp.

For multi-pattern search where correctness and O(n) worst-case are required, the Aho-Corasick automaton is preferred over rolling hash approaches.

