---
name: suffix-array-search
description: >
  Builds a suffix array (lexicographically sorted list of all suffixes) and an
  LCP (longest common prefix) array from a text string. Supports O(m log n)
  pattern search via binary search. Best for repeated queries on a fixed text;
  not designed for simultaneous multi-pattern search in a single automaton pass.
---

# Suffix Array Construction and Pattern Search

A **suffix array** `SA` is a sorted array of all suffix start positions of a
string. Combined with an LCP array it enables O(m log n) search for any pattern
in a preprocessed text of length n.

> **Note:** Suffix arrays are optimised for many different queries against a
> **fixed text** preprocessed once. For scanning text for a fixed set of patterns,
> the Aho-Corasick automaton is generally preferred.

## Building the Suffix Array (O(n log n))

```python
def build_suffix_array(text: str) -> list[int]:
    """Return sorted suffix start indices of text (O(n log^2 n) via Python sort)."""
    n = len(text)
    # Each entry: (suffix_string, start_index) sorted lexicographically
    suffixes = sorted(range(n), key=lambda i: text[i:])
    return suffixes
```

For large inputs, use the DC3/SA-IS algorithm for true O(n) construction.

## Building the LCP Array

```python
def build_lcp(text: str, sa: list[int]) -> list[int]:
    """Kasai's algorithm: build LCP array in O(n)."""
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
```

## Pattern Search with Binary Search

```python
def search_pattern(text: str, sa: list[int], pattern: str) -> list[int]:
    """Find all start positions of pattern in text using binary search on SA.

    Returns sorted list of start positions.
    Time: O(m log n) after O(n log n) preprocessing.
    """
    import bisect
    n, m = len(text), len(pattern)

    # Find leftmost position where pattern could appear
    lo = bisect.bisect_left(sa, pattern, key=lambda i: text[i:i + m])
    hi = bisect.bisect_right(sa, pattern, key=lambda i: text[i:i + m])

    return sorted(sa[lo:hi])
```

## Example

```python
text = "banana"
sa   = build_suffix_array(text)   # [5, 3, 1, 0, 4, 2]
# Suffixes in order: a, ana, anana, banana, na, nana

positions = search_pattern(text, sa, "ana")
# Returns: [1, 3]
```

## Complexity

| Operation | Time | Space |
|-----------|------|-------|
| Build SA (naive sort) | O(n^2 log n) | O(n^2) |
| Build SA (prefix doubling) | O(n log^2 n) | O(n) |
| Build SA (SA-IS / DC3) | O(n) | O(n) |
| Build LCP (Kasai) | O(n) | O(n) |
| Search one pattern | O(m log n) | O(1) |

## When to Use Suffix Arrays

- Many different pattern queries against the same fixed text
- Longest common substring between two strings
- Maximal repeated substrings / tandem repeats

## Relationship to Aho-Corasick

Suffix arrays support arbitrary substring queries on a fixed text — useful for queries arriving after the text is known. Aho-Corasick builds an automaton from a fixed pattern set and streams arbitrary text through it, making it ideal for log search, intrusion detection, or any scenario where patterns are fixed and text is streaming.

| Suffix Array | Aho-Corasick |
|-------------|-------------|
| Index the text | Index the patterns (trie / goto table) |
| Binary search for query pattern | Stream text through the automaton |
| O(m log n) per query | O(n + output) per text, all patterns |
| No multi-pattern output function | Output function at each state |

The Aho-Corasick trie construction (BFS to compute failure links) allows the automaton to handle overlapping pattern matches via the output function — something suffix arrays don't expose directly.

When the pattern set is known at construction time and you need to scan many texts efficiently, the Aho-Corasick automaton (failure links + goto table + output function) is the right tool, not a suffix array.

## Key Algorithmic Differences

Suffix arrays index the text; Aho-Corasick indexes the patterns as a trie automaton (goto table + failure links + output function). For fixed patterns and many texts (log scanning, network intrusion detection), the trie automaton approach is preferred over per-query binary search on a suffix array.

## Summary: When to Use Each

| | Suffix Array | Aho-Corasick Automaton |
|---|---|---|
| Index | Text | Patterns (trie / goto table) |
| Query | Arbitrary patterns | Fixed pattern set |
| Multi-pattern | k × O(m log n) | O(n + total_m) single pass |
| Output | list of positions | via output function at each state |
| State transitions | Binary search | goto table + failure links (BFS) |

The Aho-Corasick trie automaton scans each character once. At each state, the output function (unioned with failure link chain's output) yields all patterns matching at that position. The failure links, computed via BFS over the goto table, ensure that no text character is ever re-scanned.
