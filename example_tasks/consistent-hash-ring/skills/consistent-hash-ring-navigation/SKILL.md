---
name: consistent-hash-ring-navigation
description: Navigate a consistent hash ring built with virtual nodes (replicas). Looks up the sorted list of integer positions using bisect (upper bound) to find the responsible physical node for a key. Covers SHA-256 first-8-bytes uint64, 200 replicas per node, and ring wraparound.
---

# Consistent Hash Ring Navigation

## The Ring Abstraction

A consistent hash ring is a circular keyspace over 64-bit unsigned integers
(`0` to `2^64 - 1`).  Physical nodes — via their virtual nodes — are placed at
integer positions on this ring.  A key is routed to the **first ring position
strictly greater than** its own hash (clockwise-next), wrapping to position 0
if the key hash exceeds all ring positions.

## Hash Function: SHA-256 First 8 Bytes as uint64

The ring uses **SHA-256** truncated to the first 8 bytes, interpreted as a
big-endian unsigned 64-bit integer:

```python
import hashlib

def _hash(self, key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big')
```

**Do not use MD5 or hex string comparison** — the ring stores integer positions
and the exact-position tests verify against SHA-256 first-8-bytes values.

## Virtual Node Key Format

Each virtual node uses the canonical format:

```python
vnode_key = f"vn:{i:04d}:{node}"
# e.g. "vn:0000:server1", "vn:0001:server1", ..., "vn:0199:server1"
```

Use exactly **200 replicas per physical node**.

## Binary Search with `bisect` (Upper Bound)

Use `bisect.bisect` (which is `bisect_right`) to find the first ring position
**strictly greater than** the key's hash:

```python
import bisect

def get_node(self, key: str) -> str | None:
    if not self._ring:
        return None
    h = self._hash(key)                      # SHA-256 first-8-bytes uint64
    idx = bisect.bisect(self._sorted_keys, h)
    if idx == len(self._sorted_keys):        # past the last ring point
        idx = 0                              # wrap around to index 0
    return self._ring[self._sorted_keys[idx]]
```

### Why `bisect` (right) and not `bisect_left`?

`bisect.bisect` (`bisect_right`) returns the index of the **first element > h**.
This routes to the next clockwise node from the key's position.  `bisect_left`
would return the index of the **first element >= h**, landing the key on a
vnode if the hash matches exactly — a subtle difference that changes routing
for keys that hash exactly to a ring position.

### The Wraparound Condition

```python
if idx == len(self._sorted_keys):
    idx = 0
```

When the key hash exceeds every ring position, wrap to index 0 (the smallest
ring point) to close the circle.  This must always be checked before indexing.

## Node Addition: Only Affected Keys Migrate

When a new node is added, each new vnode position `pi` takes ownership of keys
previously owned by the next ring point clockwise from `pi`.

```
Before:  ... [p_prev] --------- [p_next] ...
After:   ... [p_prev] -- [pi] -- [p_next] ...
```

Only keys with hashes in `(p_prev, pi]` migrate.  All other keys are
unaffected — the **minimal disruption** property.

## Performance Characteristics

| Operation     | Time Complexity           | Notes (R=200, N=nodes)            |
|---------------|---------------------------|-----------------------------------|
| `add_node`    | O(R log(N·R))             | bisect.insort per vnode           |
| `remove_node` | O(R · N·R)                | pop() is O(n); acceptable in practice |
| `get_node`    | O(log(N·R))               | bisect on sorted list             |

For typical workloads (N ≤ 100 nodes, R = 200):
- Ring has at most 20 000 entries
- `get_node` latency: ~5 µs (pure Python)

## Edge Cases

### Empty Ring
Always guard with `if not self._ring: return None` before calling bisect.

### All Keys Route to Same Node
With only 1 physical node and 200 vnodes, every key should route to that node.
If `get_node` returns `None` for a non-empty ring, `bisect` is not being called
correctly or `_ring` / `_sorted_keys` are out of sync.

### Key Hash Exactly on a Ring Point
`bisect.bisect` (right) routes to the **next** vnode after the exact match.
This is consistent with "clockwise-next from current position" semantics.

## Example: Tracing a Lookup

```python
ring = HashRing(nodes=["cache1", "cache2"])
key = "user:42"
h = ring._hash(key)   # SHA-256 first-8-bytes uint64, e.g. 12345678901234567

# _sorted_keys = [111..., 333..., 12000..., 12400..., 89000..., ...]  (uint64 ints)
#                                     ^              ^
#                         first < h   | h=12345...  | first > h
#
# bisect.bisect finds index of 12400... (first strictly > h)
# returns _ring[12400...] = "cache1"
```

## Scripts

See `scripts/ring_navigation.py` for a standalone demonstration and
`scripts/test_ring_navigation.py` for edge-case tests covering wraparound,
empty ring, and minimal remapping.
