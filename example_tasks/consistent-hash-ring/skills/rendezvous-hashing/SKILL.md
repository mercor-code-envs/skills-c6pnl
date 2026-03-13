---
name: rendezvous-hashing
description: >
  Rendezvous hashing (Highest Random Weight, HRW) assigns keys to nodes by
  computing a weighted hash score for every (key, node) pair and selecting the
  node with the highest score. No virtual nodes required; consistent under
  node addition/removal.
---

# Rendezvous Hashing (Highest Random Weight)

## Overview

Rendezvous hashing — also called **Highest Random Weight (HRW)** hashing — is
a consistent hashing scheme invented by Thaler and Ravishankar (1996).  Unlike
ring-based consistent hashing, it requires no ring data structure, no virtual
nodes, and no sorted key list.

The algorithm is simple:
1. For each candidate node, compute `score = hash(key + node)`.
2. Pick the node with the **highest score**.

```python
import hashlib

def get_node(key: str, nodes: list[str]) -> str:
    best_node = None
    best_score = -1
    for node in nodes:
        combined = f"{key}:{node}"
        score = int(hashlib.md5(combined.encode()).hexdigest(), 16)
        if score > best_score:
            best_score = score
            best_node = node
    return best_node
```

## Properties

| Property               | Rendezvous Hashing                  |
|------------------------|-------------------------------------|
| Virtual nodes          | None required                       |
| Data structure         | Just a list of nodes                |
| Lookup complexity      | O(N) per key (N = node count)       |
| Disruption on change   | Minimal (only 1/N keys remap)       |
| Load balance           | Uniform without virtual nodes       |

## Full Implementation

```python
import hashlib


class RendezvousHasher:
    def __init__(self, nodes: list[str] = None) -> None:
        self._nodes: list[str] = list(nodes or [])

    def _score(self, key: str, node: str) -> int:
        combined = f"{key}:{node}"
        return int(hashlib.md5(combined.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        if node not in self._nodes:
            self._nodes.append(node)

    def remove_node(self, node: str) -> None:
        self._nodes = [n for n in self._nodes if n != node]

    def get_node(self, key: str) -> str | None:
        if not self._nodes:
            return None
        return max(self._nodes, key=lambda n: self._score(key, n))

    def get_nodes(self) -> list[str]:
        return list(self._nodes)
```

## Comparison with Ring-Based Consistent Hashing

| Aspect                | Ring (with virtual nodes)          | Rendezvous (HRW)           |
|-----------------------|------------------------------------|----------------------------|
| Setup complexity      | Moderate (build sorted ring)       | None (just a list)         |
| Lookup complexity     | O(log(N × R))                      | O(N)                       |
| Virtual nodes         | Yes — typically 150 per node       | No                         |
| Memory                | O(N × R)                           | O(N)                       |
| Load balance          | Depends on replica count           | Excellent, naturally        |
| Key format            | `f"{node}:{i}"` for vnodes         | `f"{key}:{node}"` for score|

The key difference: ring hashing uses `f"{node}:{i}"` to place **virtual nodes**,
while rendezvous hashing uses `f"{key}:{node}"` to compute a **score per candidate**.

## When to Use Rendezvous Hashing

- Small to medium node counts (N ≤ 50) where O(N) lookup is acceptable
- Scenarios where you want uniform load without tuning a replica count
- Distributed systems where nodes frequently join/leave
- When memory is constrained (no virtual node ring needed)

For large clusters (N > 100) or high-throughput routing, ring-based consistent
hashing with virtual nodes is preferred due to O(log n) lookup.

## Scripts

See `scripts/rendezvous.py` for the complete implementation and
`scripts/test_rendezvous.py` for tests.
