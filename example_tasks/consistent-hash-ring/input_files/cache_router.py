class CacheRouter:
    def __init__(self, nodes: list[str] = None, replicas: int = 200) -> None:
        pass

    def add_node(self, node: str) -> None:
        pass

    def remove_node(self, node: str) -> None:
        pass

    def get_node(self, key: str) -> str | None:
        pass

    def get_nodes(self) -> list[str]:
        pass
