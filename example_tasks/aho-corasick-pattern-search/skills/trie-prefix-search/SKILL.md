---
name: trie-prefix-search
description: >
  Builds a trie (prefix tree) that supports O(m) insert, O(m) exact lookup,
  and O(m + k) prefix search returning all words with a given prefix.
  A plain trie has no failure links and no output union — it cannot scan
  arbitrary text for multiple patterns; use Aho-Corasick for that.
---

# Trie (Prefix Tree) for Dictionary and Prefix Search

A trie stores a set of strings so that all words sharing a common prefix share
the same initial path. This enables O(m) insert, O(m) lookup, and efficient
prefix queries.

> **Important:** A plain trie supports prefix queries on a **dictionary** of
> words. It cannot scan arbitrary text for all pattern occurrences. For that
> use case (multi-pattern substring search) the **Aho-Corasick** algorithm
> extends the trie with failure links and an output function.

## Trie Node

```python
class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False
```

## Trie Operations

```python
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie. O(m)."""
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        """Return True if word is in the trie (exact match). O(m)."""
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any word in the trie starts with prefix. O(m)."""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True

    def words_with_prefix(self, prefix: str) -> list[str]:
        """Return all words in the trie that start with prefix. O(m + k)."""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        results: list[str] = []
        self._dfs(node, list(prefix), results)
        return results

    def _dfs(self, node: TrieNode, path: list[str], results: list[str]) -> None:
        if node.is_end:
            results.append("".join(path))
        for ch, child in node.children.items():
            path.append(ch)
            self._dfs(child, path, results)
            path.pop()
```

## Example

```python
trie = Trie()
for word in ["apple", "app", "application", "apply", "banana"]:
    trie.insert(word)

trie.search("app")           # True
trie.search("ap")            # False
trie.starts_with("app")      # True
trie.words_with_prefix("app")
# Returns: ["app", "apple", "application", "apply"] (order may vary)
```

## Complexity

| Operation | Time | Space |
|-----------|------|-------|
| Insert | O(m) | O(m) per word |
| Exact search | O(m) | O(1) |
| Prefix check | O(m) | O(1) |
| All words with prefix | O(m + k) | O(k) for output |
| Total space | — | O(sum of word lengths) |

## Difference from Aho-Corasick

| Feature | Plain Trie | Aho-Corasick |
|---------|-----------|--------------|
| Failure links | No | Yes (BFS-built) |
| Output union | No | Yes |
| Scan arbitrary text | No | Yes |
| Multi-pattern substring search | No | Yes |
| Use case | Dictionary / autocomplete | Log analysis / intrusion detection |

## Relationship to Aho-Corasick

A basic trie supports prefix queries and exact lookups by sharing a goto table (character-to-child mapping) among all inserted strings. Aho-Corasick extends a trie into a full pattern-matching automaton by adding two additional structures:

1. **Failure links** — computed via BFS over the trie; each state's failure link points to the longest proper suffix of that state's string that is also a prefix of some pattern. This allows the automaton to continue matching without backtracking in the text.

2. **Output function** — at each trie state, the output function accumulates all patterns that end at that state or at any state reachable via the failure-link chain.

A plain trie without failure links requires re-scanning the text from the next character after every mismatch — O(n * m) in the worst case. The BFS-computed failure links reduce this to O(n + total_match_output), making the full Aho-Corasick automaton strictly more powerful for pattern matching than a bare trie.

Use a trie for autocomplete, prefix grouping, or dictionary lookups. Use Aho-Corasick (trie + failure links + output function) when you need efficient multi-pattern text matching.

