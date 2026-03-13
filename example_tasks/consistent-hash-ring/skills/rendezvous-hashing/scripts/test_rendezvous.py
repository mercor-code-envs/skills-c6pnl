"""Unit tests for rendezvous.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from rendezvous import RendezvousHasher


def test_empty():
    h = RendezvousHasher()
    assert h.get_node("key") is None


def test_single_node():
    h = RendezvousHasher(nodes=["only"])
    for i in range(50):
        assert h.get_node(f"k{i}") == "only"


def test_deterministic():
    h = RendezvousHasher(nodes=["a", "b", "c"])
    keys = [f"key_{i}" for i in range(100)]
    r1 = [h.get_node(k) for k in keys]
    r2 = [h.get_node(k) for k in keys]
    assert r1 == r2


def test_minimal_remapping():
    h = RendezvousHasher(nodes=["x", "y", "z"])
    keys = [f"k{i}" for i in range(1000)]
    before = {k: h.get_node(k) for k in keys}
    h.remove_node("y")
    after = {k: h.get_node(k) for k in keys}
    for k in keys:
        if before[k] != after[k]:
            assert before[k] == "y"


def test_load_distribution():
    h = RendezvousHasher(nodes=[f"node{i}" for i in range(10)])
    counts: dict[str, int] = {}
    for i in range(10_000):
        n = h.get_node(f"key_{i}")
        counts[n] = counts.get(n, 0) + 1
    ratio = max(counts.values()) / min(counts.values())
    assert ratio < 2.0


def test_get_nodes():
    h = RendezvousHasher(nodes=["a", "b", "c"])
    assert set(h.get_nodes()) == {"a", "b", "c"}


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
