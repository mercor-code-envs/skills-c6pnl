"""Tests for MultiPatternSearch multi-pattern search implementation."""
import sys
import pytest

sys.path.insert(0, "/app")
from log_search import MultiPatternSearch


# ---------------------------------------------------------------------------
# API shape tests — these are the primary discriminators
# ---------------------------------------------------------------------------

def test_find_all_returns_dict():
    """find_all() must return a dict, not a list."""
    engine = MultiPatternSearch(["he", "she", "hers"])
    result = engine.find_all("ushers")
    assert isinstance(result, dict), (
        "find_all() must return dict[str, list[int]], got: " + str(type(result))
    )


def test_find_all_dict_values_are_lists():
    """find_all() dict values must be lists of ints (start positions)."""
    engine = MultiPatternSearch(["he"])
    result = engine.find_all("hello")
    assert "he" in result
    assert isinstance(result["he"], list)
    assert result["he"] == [0]


def test_find_any_returns_tuple_or_none():
    """find_any() must return a (int, str) tuple or None."""
    engine = MultiPatternSearch(["he", "she"])
    result = engine.find_any("ushers")
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], int)
    assert isinstance(result[1], str)


def test_find_any_returns_none_on_no_match():
    """find_any() must return None when no patterns match."""
    engine = MultiPatternSearch(["xyz"])
    assert engine.find_any("hello world") is None


# ---------------------------------------------------------------------------
# find_all() correctness tests
# ---------------------------------------------------------------------------

def test_find_all_basic():
    """Classic Aho-Corasick example: patterns in 'ushers'."""
    engine = MultiPatternSearch(["he", "she", "his", "hers"])
    result = engine.find_all("ushers")
    assert result == {"she": [1], "he": [2], "hers": [2]}


def test_find_all_no_match_patterns_absent():
    """Patterns with no matches must NOT appear as keys."""
    engine = MultiPatternSearch(["he", "she", "his", "hers"])
    result = engine.find_all("ushers")
    assert "his" not in result


def test_find_all_single_pattern_found():
    engine = MultiPatternSearch(["he"])
    result = engine.find_all("ahers")
    assert result == {"he": [1]}


def test_find_all_pattern_at_start():
    engine = MultiPatternSearch(["he"])
    result = engine.find_all("hello")
    assert result == {"he": [0]}


def test_find_all_pattern_at_end():
    engine = MultiPatternSearch(["rs"])
    result = engine.find_all("ushers")
    assert result == {"rs": [4]}


def test_find_all_no_match():
    engine = MultiPatternSearch(["xyz"])
    assert engine.find_all("hello world") == {}


def test_find_all_overlapping_same_pattern():
    """'aa' in 'aaa' should find 2 overlapping matches."""
    engine = MultiPatternSearch(["aa"])
    result = engine.find_all("aaa")
    assert result == {"aa": [0, 1]}


def test_find_all_overlapping_different_patterns():
    engine = MultiPatternSearch(["abcde", "bcde", "cde"])
    result = engine.find_all("abcde")
    assert result == {"abcde": [0], "bcde": [1], "cde": [2]}


def test_find_all_multiple_occurrences():
    engine = MultiPatternSearch(["ab"])
    result = engine.find_all("ababab")
    assert result == {"ab": [0, 2, 4]}


def test_find_all_empty_text():
    engine = MultiPatternSearch(["he", "she"])
    assert engine.find_all("") == {}


def test_find_all_empty_patterns():
    engine = MultiPatternSearch([])
    assert engine.find_all("hello") == {}


def test_find_all_empty_pattern_ignored():
    """Empty patterns must be silently ignored."""
    engine = MultiPatternSearch(["", "he"])
    result = engine.find_all("hello")
    assert "he" in result
    assert "" not in result


def test_find_all_pattern_longer_than_text():
    engine = MultiPatternSearch(["toolongpattern"])
    assert engine.find_all("short") == {}


def test_find_all_case_sensitive():
    engine = MultiPatternSearch(["He"])
    result = engine.find_all("he He")
    assert "He" in result
    assert result["He"] == [3]
    assert "he" not in result


def test_find_all_suffix_via_failure_link():
    """A pattern that is a suffix of a longer pattern must be found."""
    engine = MultiPatternSearch(["she", "he"])
    result = engine.find_all("she")
    assert "she" in result
    assert "he" in result
    assert result["she"] == [0]
    assert result["he"] == [1]


def test_find_all_shared_prefix_patterns():
    engine = MultiPatternSearch(["a", "ab", "abc", "abcd"])
    result = engine.find_all("abcd")
    assert result == {"a": [0], "ab": [0], "abc": [0], "abcd": [0]}


def test_find_all_pattern_equals_text():
    engine = MultiPatternSearch(["hello"])
    assert engine.find_all("hello") == {"hello": [0]}


# ---------------------------------------------------------------------------
# find_any() correctness tests
# ---------------------------------------------------------------------------

def test_find_any_basic():
    """find_any() returns first match by position."""
    engine = MultiPatternSearch(["he", "she", "hers"])
    result = engine.find_any("ushers")
    # "she" starts at position 1, "he" at 2, "hers" at 2 — first is (1, "she")
    assert result == (1, "she")


def test_find_any_tie_broken_by_shortest():
    """When two patterns match at the same earliest position, shortest wins."""
    engine = MultiPatternSearch(["he", "hers"])
    result = engine.find_any("hers")
    # both "he" and "hers" start at 0; shortest is "he"
    assert result == (0, "he")


def test_find_any_single_pattern():
    engine = MultiPatternSearch(["world"])
    result = engine.find_any("hello world")
    assert result == (6, "world")


def test_find_any_empty_text():
    engine = MultiPatternSearch(["he"])
    assert engine.find_any("") is None


def test_find_any_empty_patterns():
    engine = MultiPatternSearch([])
    assert engine.find_any("hello") is None


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-rA"])
    print("pass" if exit_code == 0 else "fail")
    sys.exit(exit_code)
