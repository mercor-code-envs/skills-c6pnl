"""
Rendezvous hashing (Highest Random Weight) implementation.
Each key is assigned to the node with the highest hash(key:node) score.
"""
import hashlib


class RendezvousHasher:
    """
    Highest Random Weight (HRW) consistent hashing.

    No virtual nodes, no sorted ring. Just compute a score for each
    (key, node) pair and pick the node with the maximum score.
    """

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


if __name__ == "__main__":
    hasher = RendezvousHasher(nodes=["cache1", "cache2", "cache3"])
    counts: dict[str, int] = {}
    for i in range(10_000):
        node = hasher.get_node(f"key_{i}")
        counts[node] = counts.get(node, 0) + 1

    print("Rendezvous hashing load distribution (10k keys, 3 nodes):")
    for node, count in sorted(counts.items()):
        print(f"  {node}: {count}")
    ratio = max(counts.values()) / min(counts.values())
    print(f"max/min ratio: {ratio:.2f}")
