"""
Modulo hash sharding: hash(key) % N.
Simple but causes mass remapping when N changes.
"""
import hashlib


class ModuloShardRouter:
    """
    Naive modulo hash router.

    CAUTION: Adding or removing nodes causes approximately (N-1)/N keys
    to remap — catastrophic for caches. Use consistent hashing for dynamic
    node sets.
    """

    def __init__(self, nodes: list[str] = None) -> None:
        self._nodes: list[str] = list(nodes or [])

    def _shard_index(self, key: str) -> int:
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return h % len(self._nodes)

    def add_node(self, node: str) -> None:
        """Append node. WARNING: reshuffles almost all key assignments."""
        self._nodes.append(node)

    def remove_node(self, node: str) -> None:
        """Remove node. WARNING: reshuffles almost all key assignments."""
        if node in self._nodes:
            self._nodes.remove(node)

    def get_node(self, key: str) -> str | None:
        if not self._nodes:
            return None
        return self._nodes[self._shard_index(key)]

    def get_nodes(self) -> list[str]:
        return list(self._nodes)


if __name__ == "__main__":
    nodes_3 = [f"node{i}" for i in range(3)]
    nodes_4 = [f"node{i}" for i in range(4)]
    r3 = ModuloShardRouter(nodes=nodes_3)
    r4 = ModuloShardRouter(nodes=nodes_4)

    keys = [f"key_{i}" for i in range(1000)]
    remapped = sum(1 for k in keys if r3.get_node(k) != r4.get_node(k))
    print(f"Modulo 3→4: {remapped}/1000 keys remapped ({remapped/10:.1f}%)")
    print("(Compare: consistent ring hash would remap ~250/1000 = 25%)")
