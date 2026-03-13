"""Unit tests for Aho-Corasick trie construction."""
import sys
import pytest
from ac_builder import build_automaton


def test_single_pattern_goto():
    goto, output, fail = build_automaton(["ab"])
    # root -a-> 1 -b-> 2
    assert goto[0]["a"] == 1
    assert goto[1]["b"] == 2
    assert output[2] == [0]


def test_shared_prefix():
    goto, output, fail = build_automaton(["ab", "ac"])
    # Both share state 1 after 'a'
    state_a = goto[0]["a"]
    assert "b" in goto[state_a]
    assert "c" in goto[state_a]


def test_failure_links_depth1():
    """All depth-1 nodes must have fail = 0 (root)."""
    goto, output, fail = build_automaton(["he", "she", "his", "hers"])
    for ch, s in goto[0].items():
        assert fail[s] == 0, f"Depth-1 state {s} via '{ch}' should have fail=0"


def test_output_union_she_he():
    """After building, the 'e' at end of 'she' must output both 'she' and 'he'."""
    patterns = ["she", "he"]
    goto, output, fail = build_automaton(patterns)
    # Walk to end of 'she'
    cur = goto[0]["s"]
    cur = goto[cur]["h"]
    cur = goto[cur]["e"]
    pattern_indices = output[cur]
    # Both patterns must be present
    assert 0 in pattern_indices  # "she"
    assert 1 in pattern_indices  # "he"


def test_failure_links_computed_by_bfs():
    """Failure links at depth > 1 must reference valid trie states."""
    patterns = ["abcd", "bcd", "cd"]
    goto, output, fail = build_automaton(patterns)
    # Walk down "abcd"
    states = [0]
    for ch in "abcd":
        states.append(goto[states[-1]][ch])
    # All fail links must be valid state indices
    for s in states[1:]:
        assert 0 <= fail[s] < len(goto)


def test_empty_patterns():
    goto, output, fail = build_automaton([])
    assert goto == [{}]
    assert output == [[]]
    assert fail == [0]


def test_single_char_patterns():
    goto, output, fail = build_automaton(["a", "b", "c"])
    for ch in "abc":
        s = goto[0][ch]
        assert len(output[s]) == 1


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
