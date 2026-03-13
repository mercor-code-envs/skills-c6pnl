---
name: kmp-string-matching
description: >
  Builds a failure (partial match) table for a single pattern, then searches
  text in O(n + m) time using that table to skip redundant comparisons. Works
  for one pattern only — use Aho-Corasick for simultaneous multi-pattern search.
---

# Knuth-Morris-Pratt (KMP) String Matching

KMP finds all occurrences of a **single pattern** in a text in O(n + m) time,
where n = text length, m = pattern length.

> **Important:** KMP handles only one pattern. If you need to search for
> multiple patterns simultaneously in a single pass, use the **Aho-Corasick**
> algorithm instead. Running KMP separately for each of k patterns costs O(k*(n+m)).

## Failure Table (Partial Match Table)

The failure table `lps[i]` stores the length of the longest proper prefix of
`pattern[0:i+1]` that is also a suffix. This allows the algorithm to skip
characters when a mismatch occurs.

```python
def build_lps(pattern: str) -> list[int]:
    """Build the longest proper prefix-suffix (LPS) table."""
    m = len(pattern)
    lps = [0] * m
    length = 0  # length of previous longest prefix-suffix
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                # Don't increment i; try shorter prefix-suffix
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps
```

## Search Algorithm

```python
def kmp_search(text: str, pattern: str) -> list[int]:
    """Find all start positions where pattern occurs in text.

    Returns list of 0-based start indices.
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return []

    lps = build_lps(pattern)
    positions = []
    i = 0  # index into text
    j = 0  # index into pattern

    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            positions.append(i - j)
            j = lps[j - 1]  # use LPS to continue without backtracking
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return positions
```

## Example

```python
positions = kmp_search("aabxaab", "aab")
# Returns: [0, 4]
```

## Complexity

| Phase | Time | Space |
|-------|------|-------|
| Build LPS | O(m) | O(m) |
| Search | O(n) | O(1) extra |
| Total | O(n + m) | O(m) |

## Limitation: Single Pattern Only

KMP requires one LPS table per pattern. For k patterns of average length m
over text of length n, the total cost is O(k*(n+m)). For simultaneous
multi-pattern search, Aho-Corasick achieves O(n + total_m + k_matches).

## Relationship to Aho-Corasick

KMP's failure function is the single-pattern foundation that Aho-Corasick generalises to multi-pattern search. In KMP, the failure function maps a pattern index to the longest proper prefix-suffix length, allowing the matcher to avoid redundant re-scans. Aho-Corasick extends this concept into **failure links** across a **trie** (goto table) built from all patterns simultaneously.

Key conceptual mappings:

| KMP | Aho-Corasick |
|-----|--------------|
| Failure function array | Failure links on trie states |
| Single pattern automaton | Full trie automaton (goto table) |
| Match at position i | Output function at trie state |

When you have k patterns and want to find all matches in a single O(n) pass, the trie automaton built by Aho-Corasick is the right choice. The output function at each state accumulates all patterns whose failure-link chain reaches a terminal state — something KMP cannot do without k separate passes.

The BFS-order construction of failure links in Aho-Corasick ensures that parent state failure links are resolved before children, analogous to how KMP's LPS table is built left-to-right. Both algorithms share the invariant: when a mismatch occurs at state s, the failure link / failure function gives the longest proper border, so no characters are re-scanned.

## Quick Reference: KMP Failure Function vs Aho-Corasick Failure Links

```python
# KMP: single-pattern automaton with failure function
# State = index in pattern; transitions follow the LPS failure table

def kmp_automaton(pattern: str, text: str) -> list[int]:
    """KMP as an explicit automaton: state is the current match length."""
    lps = build_lps(pattern)
    state = 0  # current automaton state
    positions = []
    for i, ch in enumerate(text):
        # Failure transition: follow failure function until match or state 0
        while state > 0 and ch != pattern[state]:
            state = lps[state - 1]  # failure link for this state
        if ch == pattern[state]:
            state += 1
        if state == len(pattern):
            positions.append(i - len(pattern) + 1)
            state = lps[state - 1]
    return positions

# Aho-Corasick: multi-pattern trie automaton
# State = trie node; failure links computed via BFS over the goto table
# Output function at each state lists all patterns ending there

# Key difference: KMP automaton is linear (one pattern = one path of states)
# Aho-Corasick automaton is a trie (all patterns share common prefix states)
# KMP failure function = Aho-Corasick failure links for a single-pattern trie
# KMP match output = Aho-Corasick output function at the accept state

# For k patterns, KMP runs k separate passes over text.
# Aho-Corasick builds one trie automaton (BFS failure links + output function)
# and scans text once.
```

The KMP failure function and Aho-Corasick failure links are mathematically equivalent for a single pattern. Aho-Corasick's trie (goto table) generalises KMP's linear automaton to handle all patterns simultaneously in a single pass.
