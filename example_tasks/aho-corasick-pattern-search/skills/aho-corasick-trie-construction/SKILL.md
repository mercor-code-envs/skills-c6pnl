---
name: aho-corasick-trie-construction
description: >
  Builds the Aho-Corasick automaton: inserts patterns into a trie (goto function),
  then computes failure links using BFS and unions output sets along failure chains.
  BFS is mandatory — DFS gives wrong failure links for nodes at depth > 1.
---

# Aho-Corasick Trie Construction

The Aho-Corasick algorithm finds all occurrences of multiple patterns in a text
in O(n + m + k) time, where n = text length, m = total pattern length, k = matches.

## Three Core Data Structures

| Structure | Type | Purpose |
|-----------|------|---------|
| `goto[state][ch]` | `list[dict]` | Transition: state × char → state |
| `output[state]` | `list[list[int]]` | Pattern indices that end at this state |
| `fail[state]` | `list[int]` | Failure link: longest proper suffix that is a prefix |

## Step 1 — Build the Goto Function (Trie Insertion)

Insert every pattern character-by-character. Create a new state when a character
has no existing transition. Record which pattern index ends at the final state.

```python
from collections import deque

def _build_goto(patterns):
    goto = [{}]      # goto[0] is the root
    output = [[]]
    fail = [0]

    for idx, pattern in enumerate(patterns):
        cur = 0
        for ch in pattern:
            if ch not in goto[cur]:
                goto[cur][ch] = len(goto)
                goto.append({})
                output.append([])
                fail.append(0)
            cur = goto[cur][ch]
        output[cur].append(idx)   # pattern idx ends here

    return goto, output, fail
```

## Step 2 — Build the Failure Function (BFS — REQUIRED)

**BFS is mandatory.** When computing `fail[s]` for a state `s` at depth d,
we rely on `fail[parent]` already being correct. BFS processes states
level by level, so `fail[parent]` is always ready. DFS does NOT guarantee
this and produces wrong failure links for states at depth > 1.

### Algorithm

1. All depth-1 children of root get `fail = 0` (root).
2. BFS: for each state `r` and each of its children `s` via character `ch`:
   - Walk up failure links from `fail[r]` until we find a state with a `ch`
     transition, or reach root.
   - `fail[s] = goto[that_state].get(ch, 0)`
   - **Union output**: `output[s] += output[fail[s]]`  ← CRITICAL

```python
def _build_failure(goto, output, fail):
    queue = deque()

    # Depth-1 nodes: fail = root
    for ch, s in goto[0].items():
        fail[s] = 0
        queue.append(s)

    while queue:
        r = queue.popleft()
        for ch, s in goto[r].items():
            queue.append(s)

            # Find longest proper suffix of path(r)+ch that is a trie prefix
            state = fail[r]
            while state != 0 and ch not in goto[state]:
                state = fail[state]          # walk up failure chain
            fail[s] = goto[state].get(ch, 0)
            if fail[s] == s:                 # avoid self-loop at root
                fail[s] = 0

            # CRITICAL: union output with failure link's output
            # Without this, patterns that are proper suffixes of other
            # patterns will be silently missed during search.
            output[s] = output[s] + output[fail[s]]
```

## Why Output Union Matters

Suppose patterns = `["she", "he"]`. After inserting into the trie:
- Path `s→h→e` ends at state 3, `output[3] = [0]` ("she")
- Path `h→e` ends at state 2, `output[2] = [1]` ("he")

The failure link of state 3 (the `e` in "she") is state 2 (the `e` in "he"),
because "he" is the longest suffix of "she" that is a prefix of a pattern.

Without output union: scanning "she" reaches state 3 and reports only "she".
With output union: `output[3] = [0, 1]`, so both "she" and "he" are reported.

## Implementation Outline

Follow this two-phase structure:

1. **Build the goto function** (trie insertion) as shown in Step 1
2. **Build the failure function** (BFS) as shown in Step 2
3. After construction, the search algorithm uses these three structures to traverse the automaton

## Common Mistakes

| Mistake | Symptom |
|---------|---------|
| Using DFS instead of BFS for failure function | Wrong failure links at depth > 1; misses patterns |
| Forgetting output union | Patterns that are suffixes of other patterns never found |
| Not handling the root specially in failure walk | Infinite loop or index error |
| `fail[s] = s` (self-loop at root char) | Infinite loop during search |
