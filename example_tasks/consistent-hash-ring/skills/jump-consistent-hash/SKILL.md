---
name: jump-consistent-hash
description: >
  Jump consistent hash maps a 64-bit key to one of N buckets in O(ln N) time
  using a single loop with no virtual nodes, no ring structure, and no memory
  allocation. Returns a bucket index, not a node name — requires a separate
  node list.
---

# Jump Consistent Hash

## Overview

Jump consistent hash, published by Lamping and Veach (2014), is a
minimal, stateless consistent hash algorithm.  Given a 64-bit integer key and
a bucket count N, it returns a bucket index in `[0, N)` in O(ln N) time using
no data structures at all.

The algorithm "jumps" forward through bucket assignments using a pseudorandom
sequence derived from the key itself.

## The Algorithm

```python
def jump_hash(key: int, num_buckets: int) -> int:
    """
    Map a 64-bit integer key to a bucket in [0, num_buckets).

    Args:
        key: 64-bit unsigned integer key
        num_buckets: number of buckets (must be >= 1)

    Returns:
        Bucket index in [0, num_buckets)
    """
    b = -1
    j = 0
    while j < num_buckets:
        b = j
        key = (key * 2862933555777941757 + 1) & 0xFFFFFFFFFFFFFFFF
        j = int((b + 1) * (2**31 / ((key >> 33) + 1)))
    return b
```

The magic constant `2862933555777941757` is a linear congruential generator
multiplier that produces good statistical properties.

## String Keys

Jump hash requires an integer key.  For string keys, hash first:

```python
import hashlib
import struct

def string_to_int64(key: str) -> int:
    digest = hashlib.md5(key.encode()).digest()
    return struct.unpack('<Q', digest[:8])[0]  # little-endian 64-bit

def jump_hash_str(key: str, num_buckets: int) -> int:
    return jump_hash(string_to_int64(key), num_buckets)
```

## Full Node Routing

```python
class JumpHashRouter:
    def __init__(self, nodes: list[str] = None) -> None:
        self._nodes: list[str] = list(nodes or [])

    def _key_to_int(self, key: str) -> int:
        import hashlib, struct
        digest = hashlib.md5(key.encode()).digest()
        return struct.unpack('<Q', digest[:8])[0]

    def add_node(self, node: str) -> None:
        self._nodes.append(node)

    def remove_node(self, node: str) -> None:
        # Note: jump hash by index — removing non-last node reshuffles
        # In practice, use tombstoning or only remove the last node
        if node in self._nodes:
            self._nodes.remove(node)

    def get_node(self, key: str) -> str | None:
        if not self._nodes:
            return None
        idx = jump_hash(self._key_to_int(key), len(self._nodes))
        return self._nodes[idx]

    def get_nodes(self) -> list[str]:
        return list(self._nodes)
```

## Key Differences from Ring-Based Consistent Hashing

| Aspect                  | Jump Hash                         | Ring Hash (virtual nodes)      |
|-------------------------|-----------------------------------|--------------------------------|
| Data structure          | None (stateless)                  | Sorted ring + dict             |
| Virtual nodes           | None                              | 150 per physical node          |
| Lookup                  | O(ln N)                           | O(log(N × R))                  |
| Memory                  | O(1)                              | O(N × R)                       |
| Key format              | Integer (hash string to int64)    | `f"{node}:{i}"` for vnodes     |
| Minimal disruption      | Only when adding at the end       | Full (any addition/removal)    |
| Node removal            | Problematic for non-last nodes    | Clean for any node             |

## Important Limitation

Jump hash is ideal when nodes are added/removed at the **end of the list only**
(append-only or shrink-from-end).  If a middle node is removed, all subsequent
bucket assignments shift, causing widespread remapping — the opposite of
minimal disruption.

For arbitrary node addition and removal, use ring-based consistent hashing with
virtual nodes.

## When to Use Jump Hash

- Shard assignment for databases with append-only scaling
- Workloads where the node list only grows
- Memory-constrained environments (no ring structure in RAM)
- Hash sharding into a fixed number of buckets

## Scripts

See `scripts/jump_hash.py` for the complete implementation and
`scripts/test_jump_hash.py` for tests verifying distribution and consistency.
