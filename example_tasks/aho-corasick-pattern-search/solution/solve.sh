#!/usr/bin/env bash
set -euo pipefail
cat > /app/log_search.py << 'PYEOF'
from collections import deque


class MultiPatternSearch:
    def __init__(self, patterns: list[str]) -> None:
        """Build automaton. Empty patterns are silently ignored."""
        self._patterns = [p for p in patterns if p]
        self._goto = [{}]
        self._output = [[]]
        self._fail = [0]
        self._build()

    def _build(self) -> None:
        for idx, pattern in enumerate(self._patterns):
            cur = 0
            for ch in pattern:
                if ch not in self._goto[cur]:
                    self._goto[cur][ch] = len(self._goto)
                    self._goto.append({})
                    self._output.append([])
                    self._fail.append(0)
                cur = self._goto[cur][ch]
            self._output[cur].append(idx)

        queue = deque()
        for ch, s in self._goto[0].items():
            self._fail[s] = 0
            queue.append(s)

        while queue:
            r = queue.popleft()
            for ch, s in self._goto[r].items():
                queue.append(s)
                state = self._fail[r]
                while state != 0 and ch not in self._goto[state]:
                    state = self._fail[state]
                self._fail[s] = self._goto[state].get(ch, 0)
                if self._fail[s] == s:
                    self._fail[s] = 0
                self._output[s] = self._output[s] + self._output[self._fail[s]]

    def find_all(self, text: str) -> dict[str, list[int]]:
        """Find all occurrences of all patterns.

        Returns dict mapping pattern -> sorted list of start positions.
        Patterns with no matches are NOT included in the result.
        """
        result: dict[str, list[int]] = {}
        cur = 0
        for i, ch in enumerate(text):
            while cur != 0 and ch not in self._goto[cur]:
                cur = self._fail[cur]
            cur = self._goto[cur].get(ch, 0)
            for pattern_idx in self._output[cur]:
                pattern = self._patterns[pattern_idx]
                start = i + 1 - len(pattern)
                if pattern not in result:
                    result[pattern] = []
                result[pattern].append(start)
        return result

    def find_any(self, text: str) -> tuple[int, str] | None:
        """Find the first match (earliest start position).

        Returns (start_position, pattern) or None if no matches.
        When multiple patterns match at the same earliest position,
        returns the shortest pattern.
        """
        all_matches = []
        cur = 0
        for i, ch in enumerate(text):
            while cur != 0 and ch not in self._goto[cur]:
                cur = self._fail[cur]
            cur = self._goto[cur].get(ch, 0)
            for pattern_idx in self._output[cur]:
                pattern = self._patterns[pattern_idx]
                start = i + 1 - len(pattern)
                all_matches.append((start, len(pattern), pattern))
        if not all_matches:
            return None
        all_matches.sort(key=lambda x: (x[0], x[1]))
        start, _, pattern = all_matches[0]
        return (start, pattern)
PYEOF
echo "Solution installed at /app/log_search.py"
