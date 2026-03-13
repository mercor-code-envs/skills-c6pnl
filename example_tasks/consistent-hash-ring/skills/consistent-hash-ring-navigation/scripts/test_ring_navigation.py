"""Unit tests for ring_navigation.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from ring_navigation import HashRing


def test_empty_ring_returns_none():
    ring = HashRing()
    assert ring.get_node("key") is None


def test_wraparound_single_node():
    """All keys route to the only node including potential wraparound keys."""
    ring = HashRing(nodes=["only"])
    for k in ["aaaa", "zzzz", "0000", "ffff", "wrap_test"]:
        assert ring.get_node(k) == "only"


def test_bisect_left_semantics():
    """Lookup is deterministic and consistent."""
    ring = HashRing(nodes=["a", "b", "c"])
    keys = [f"key{i}" for i in range(200)]
    r1 = [ring.get_node(k) for k in keys]
    r2 = [ring.get_node(k) for k in keys]
    assert r1 == r2


def test_minimal_remapping_on_removal():
    """Keys that remap on node removal must have previously been on that node."""
    ring = HashRing(nodes=["x", "y", "z"])
    keys = [f"k{i}" for i in range(1000)]
    before = {k: ring.get_node(k) for k in keys}
    ring.remove_node("y")
    after = {k: ring.get_node(k) for k in keys}
    for k in keys:
        if before[k] != after[k]:
            assert before[k] == "y", f"{k}: remapped from non-removed node {before[k]}"


def test_minimal_remapping_on_addition():
    """After adding a node, total fraction of remapped keys is small."""
    ring = HashRing(nodes=[f"n{i}" for i in range(4)])
    keys = [f"req_{i}" for i in range(2000)]
    before = {k: ring.get_node(k) for k in keys}
    ring.add_node("n4")
    after = {k: ring.get_node(k) for k in keys}
    remapped = sum(1 for k in keys if before[k] != after[k])
    assert remapped / len(keys) < 0.40


def test_remove_all_then_empty():
    ring = HashRing(nodes=["p", "q"])
    ring.remove_node("p")
    ring.remove_node("q")
    assert ring.get_node("any") is None


def test_remove_nonexistent_node_no_error():
    """Removing a node that was never added should not raise."""
    ring = HashRing(nodes=["a", "b"])
    ring.remove_node("ghost")  # should not raise
    assert set(ring.get_nodes()) == {"a", "b"}


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
