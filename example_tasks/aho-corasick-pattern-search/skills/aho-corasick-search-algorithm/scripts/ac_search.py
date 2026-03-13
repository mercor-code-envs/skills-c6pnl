"""Aho-Corasick search: traverse the automaton to find all pattern matches."""
from ac_builder import build_automaton


def search(
    text: str,
    patterns: list[str],
    goto: list[dict],
    output: list[list[int]],
    fail: list[int],
) -> list[tuple[int, int, str]]:
    """Find all occurrences of all patterns in text using the Aho-Corasick automaton.

    Args:
        text:     The text to search.
        patterns: The original list of patterns (indexed by output values).
        goto:     goto[state][ch] = next_state
        output:   output[state]   = list of pattern indices (already unioned with fail links)
        fail:     fail[state]     = failure link state

    Returns:
        Sorted list of (start, end, pattern) tuples where text[start:end] == pattern.
    """
    results: list[tuple[int, int, str]] = []
    cur = 0  # start at root

    for i, ch in enumerate(text):
        # Walk failure links until we find a valid transition or reach root
        while cur != 0 and ch not in goto[cur]:
            cur = fail[cur]

        # Take the transition (default to root if no transition from root)
        cur = goto[cur].get(ch, 0)

        # Collect all matches at this position
        # output[cur] already includes patterns from failure-link states
        for pattern_idx in output[cur]:
            pattern = patterns[pattern_idx]
            end = i + 1
            start = end - len(pattern)
            results.append((start, end, pattern))

    return sorted(results)


class AhoCorasick:
    """Complete Aho-Corasick multi-pattern search engine."""

    def __init__(self, patterns: list[str]) -> None:
        self._patterns = list(patterns)
        self._goto, self._output, self._fail = build_automaton(patterns)

    def search(self, text: str) -> list[tuple[int, int, str]]:
        """Find all occurrences of all patterns in text.

        Returns:
            Sorted list of (start, end, pattern) tuples where text[start:end] == pattern.
        """
        return search(text, self._patterns, self._goto, self._output, self._fail)
