#!/usr/bin/env bash
set -euo pipefail
cat > /app/cache_router.py << 'PYEOF'
import hashlib
import bisect


class CacheRouter:
    def __init__(self, nodes: list[str] = None, replicas: int = 200) -> None:
        self._replicas = replicas
        self._ring: dict[int, str] = {}  # hash_point -> node_name
        self._sorted_keys: list[int] = []
        for node in (nodes or []):
            self.add_node(node)

    def _hash(self, key: str) -> int:
        return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big')

    def add_node(self, node: str) -> None:
        for i in range(self._replicas):
            vnode_key = f"vn:{i:04d}:{node}"
            h = self._hash(vnode_key)
            self._ring[h] = node
            bisect.insort(self._sorted_keys, h)

    def remove_node(self, node: str) -> None:
        for i in range(self._replicas):
            vnode_key = f"vn:{i:04d}:{node}"
            h = self._hash(vnode_key)
            if h in self._ring:
                del self._ring[h]
                idx = bisect.bisect_left(self._sorted_keys, h)
                if idx < len(self._sorted_keys) and self._sorted_keys[idx] == h:
                    self._sorted_keys.pop(idx)

    def get_node(self, key: str) -> str | None:
        if not self._ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0
        return self._ring[self._sorted_keys[idx]]

    def get_nodes(self) -> list[str]:
        return list(set(self._ring.values()))
PYEOF
echo "Solution installed at /app/cache_router.py"
