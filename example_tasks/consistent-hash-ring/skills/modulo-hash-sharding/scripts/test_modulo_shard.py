"""Unit tests for modulo_shard.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from modulo_shard import ModuloShardRouter


def test_empty():
    r = ModuloShardRouter()
    assert r.get_node("key") is None


def test_single_node():
    r = ModuloShardRouter(nodes=["only"])
    for i in range(50):
        assert r.get_node(f"k{i}") == "only"


def test_deterministic():
    r = ModuloShardRouter(nodes=["a", "b", "c"])
    keys = [f"key_{i}" for i in range(100)]
    r1 = [r.get_node(k) for k in keys]
    r2 = [r.get_node(k) for k in keys]
    assert r1 == r2


def test_mass_remapping_on_add():
    """Adding a node causes most keys to remap (the core weakness)."""
    r_before = ModuloShardRouter(nodes=[f"n{i}" for i in range(3)])
    r_after = ModuloShardRouter(nodes=[f"n{i}" for i in range(4)])
    keys = [f"k{i}" for i in range(1000)]
    remapped = sum(1 for k in keys if r_before.get_node(k) != r_after.get_node(k))
    # Should be very high (>>50%) — demonstrating the weakness
    assert remapped > 500, f"Expected mass remapping, got {remapped}/1000"


def test_all_keys_get_valid_node():
    r = ModuloShardRouter(nodes=["a", "b", "c", "d"])
    nodes_set = {"a", "b", "c", "d"}
    for i in range(200):
        result = r.get_node(f"key_{i}")
        assert result in nodes_set


def test_get_nodes():
    r = ModuloShardRouter(nodes=["x", "y", "z"])
    assert set(r.get_nodes()) == {"x", "y", "z"}


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
