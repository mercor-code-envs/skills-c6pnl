"""Unit tests for the Aho-Corasick search algorithm."""
import sys
import pytest
from ac_search import AhoCorasick


def test_classic_ushers():
    ac = AhoCorasick(["he", "she", "his", "hers"])
    results = ac.search("ushers")
    assert (1, 4, "she") in results
    assert (2, 4, "he") in results
    assert (2, 6, "hers") in results
    assert len(results) == 3


def test_overlapping_aa():
    ac = AhoCorasick(["aa"])
    results = ac.search("aaa")
    assert (0, 2, "aa") in results
    assert (1, 3, "aa") in results
    assert len(results) == 2


def test_empty_text():
    ac = AhoCorasick(["abc"])
    assert ac.search("") == []


def test_empty_patterns():
    ac = AhoCorasick([])
    assert ac.search("hello") == []


def test_no_match():
    ac = AhoCorasick(["xyz"])
    assert ac.search("hello world") == []


def test_suffix_via_failure_link():
    """Pattern 'he' must be found when 'she' is also in patterns, via failure link."""
    ac = AhoCorasick(["she", "he"])
    results = ac.search("she")
    found = {p for _, _, p in results}
    assert "she" in found
    assert "he" in found


def test_slice_invariant():
    text = "ushers aab aaa"
    patterns = ["he", "she", "his", "hers", "aa", "aab"]
    ac = AhoCorasick(patterns)
    for start, end, pattern in ac.search(text):
        assert text[start:end] == pattern


def test_results_sorted():
    ac = AhoCorasick(["b", "a", "ab"])
    results = ac.search("aab")
    assert results == sorted(results)


def test_pattern_at_start():
    ac = AhoCorasick(["he"])
    results = ac.search("hello")
    assert (0, 2, "he") in results


def test_pattern_at_end():
    ac = AhoCorasick(["lo"])
    results = ac.search("hello")
    assert (3, 5, "lo") in results


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
