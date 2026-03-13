"""Plain trie (prefix tree) supporting insert, search, prefix queries."""


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False


class Trie:
    """Prefix tree for dictionary storage and prefix queries."""

    def __init__(self) -> None:
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
        return sorted(results)

    def _dfs(self, node: TrieNode, path: list[str], results: list[str]) -> None:
        if node.is_end:
            results.append("".join(path))
        for ch, child in sorted(node.children.items()):
            path.append(ch)
            self._dfs(child, path, results)
            path.pop()
