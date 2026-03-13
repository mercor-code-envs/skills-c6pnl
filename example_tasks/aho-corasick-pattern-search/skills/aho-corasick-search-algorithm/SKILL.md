---
name: aho-corasick-search-algorithm
description: >
  Traverses the Aho-Corasick automaton over input text to find all pattern
  occurrences in O(n + k) time using the goto table, failure links, and output
  function.
---

# Aho-Corasick Search Algorithm

Once the automaton is built (see `aho-corasick-trie-construction`), scanning
text for all patterns takes a single O(n) pass with no backtracking.


## Core Search Loop

The underlying traversal is shared by both methods:

```python
cur = 0  # start at root

for i, ch in enumerate(text):
    # Follow failure links until we find a valid transition or reach root
    while cur != 0 and ch not in self._goto[cur]:
        cur = self._fail[cur]

    # Take the transition (stay at root if no transition from root)
    cur = self._goto[cur].get(ch, 0)

    # Collect all matches: output[cur] already includes failure-link outputs
    for pattern_idx in self._output[cur]:
        pattern = self._patterns[pattern_idx]
        start = i + 1 - len(pattern)
        # record (start, pattern)
```

## Key Implementation Points

### 1. Failure Link Walk Before Transition

When the current state has no transition for `ch`, walk up failure links until:
- We find a state that **does** have a transition for `ch`, OR
- We reach the root (state 0)

Only then take the `goto[cur].get(ch, 0)` transition (defaulting to root).

### 2. Output Function Already Includes Failure-Link Outputs

The `output[s]` list was unioned with `output[fail[s]]` during construction
(see `aho-corasick-trie-construction`). You do NOT need to walk failure links
again during the output collection phase.

### 3. Computing start from Position i

`i` is the 0-based index of the current character. When `output[cur]` contains
a pattern of length L, the match starts at `i + 1 - L`:

```python
start = i + 1 - len(pattern)
```

### 4. Empty Patterns Must Be Ignored

Filter out empty patterns in `__init__` before building the automaton:

```python
self._patterns = [p for p in patterns if p]
```


## Complexity

| Phase | Time |
|-------|------|
| Construction | O(m) where m = total length of all patterns |
| Search | O(n + k) where n = text length, k = number of matches |
| Total | O(n + m + k) |

## See Also

- `aho-corasick-trie-construction` — building the automaton (goto, fail, output)
