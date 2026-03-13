---
name: modulo-hash-sharding
description: >
  Simple modulo hash sharding assigns keys to shards using hash(key) % N.
  Easy to implement but causes massive key remapping when N changes. Covers
  the algorithm, its limitations, and when to use it despite the drawbacks.
---

# Modulo Hash Sharding

## Overview

Modulo hash sharding is the simplest approach to distributing keys across a
fixed set of nodes.  Given N nodes, a key `k` maps to node index `hash(k) % N`.

```python
import hashlib

def get_shard(key: str, num_nodes: int) -> int:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return h % num_nodes
```

No virtual nodes, no ring, no sorted lists.  Just arithmetic.

## Full Implementation

```python
import hashlib


class ModuloShardRouter:
    """
    Naive modulo hash router.
    WARNING: Adding or removing nodes causes ~(N-1)/N keys to remap.
    Use only for fixed, static node counts.
    """

    def __init__(self, nodes: list[str] = None) -> None:
        self._nodes: list[str] = list(nodes or [])

    def _shard_index(self, key: str) -> int:
        if not self._nodes:
            return -1
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return h % len(self._nodes)

    def add_node(self, node: str) -> None:
        self._nodes.append(node)
        # WARNING: this changes routing for almost all existing keys

    def remove_node(self, node: str) -> None:
        if node in self._nodes:
            self._nodes.remove(node)
        # WARNING: this changes routing for almost all existing keys

    def get_node(self, key: str) -> str | None:
        if not self._nodes:
            return None
        return self._nodes[self._shard_index(key)]

    def get_nodes(self) -> list[str]:
        return list(self._nodes)
```

## The Fatal Flaw: Mass Remapping

When the node count changes from N to N+1, almost every key changes its
assignment:

```
3 nodes: key_1 → hash % 3 = 2 → node2
4 nodes: key_1 → hash % 4 = 3 → node3  (different!)
```

For N=10 → N=11:
- Expected fraction that remaps: approximately (N-1)/N ≈ **90%**
- For N=100 → N=101: ~99% of keys remap

Compare to consistent hashing where only ~1/N keys remap (10% for 10→11 nodes).

```python
# Demonstration of the remapping problem
nodes_before = [f"node{i}" for i in range(3)]
nodes_after = [f"node{i}" for i in range(4)]

router_before = ModuloShardRouter(nodes=nodes_before)
router_after = ModuloShardRouter(nodes=nodes_after)

keys = [f"key_{i}" for i in range(1000)]
remapped = sum(
    1 for k in keys
    if router_before.get_node(k) != router_after.get_node(k)
)
print(f"Remapped: {remapped}/1000 ({remapped/10:.1f}%)")
# Output: Remapped: ~750/1000 (75.0%) — catastrophic for a cache
```

## When to Use Modulo Sharding

Despite the remapping problem, modulo sharding is appropriate when:

1. **Node count is fixed and never changes** — database sharding at deploy time
2. **Resharding is acceptable** — offline migrations with full data copy
3. **Simplicity trumps consistency** — prototypes, small internal tools
4. **Read-heavy with cold start OK** — cache miss on reshard is tolerable

## Comparison with Consistent Hashing

| Property            | Modulo Sharding          | Consistent Ring Hash     |
|---------------------|--------------------------|--------------------------|
| Implementation      | 1 line: `hash % N`       | Sorted ring + bisect     |
| Virtual nodes       | None                     | 150 per physical node    |
| Remap on add        | ~(N-1)/N of all keys     | ~1/(N+1) of all keys     |
| Remap on remove     | ~(N-1)/N of all keys     | ~1/N of all keys         |
| Load balance        | Excellent (uniform)      | Good (needs 150 replicas)|
| Key format          | Just the key itself      | `f"{node}:{i}"` for ring |

## Sharding with Consistent Hashing

For production distributed systems that require dynamic scaling without full
resharding, use consistent hashing with virtual nodes instead:

- Ring hash: add 1 node → ~1/(N+1) keys remap
- Modulo hash: add 1 node → ~N/(N+1) keys remap

The difference matters enormously for caches, where a cache miss causes a
backend request: consistent hashing keeps cache hit rates high during scaling.

## Scripts

See `scripts/modulo_shard.py` for the implementation and
`scripts/test_modulo_shard.py` for tests demonstrating the remapping problem.
