"""Huffman coding: frequency-based variable-length compression."""
import heapq
from collections import Counter


class HuffmanNode:
    def __init__(self, char: str | None, freq: int,
                 left: 'HuffmanNode | None' = None,
                 right: 'HuffmanNode | None' = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'HuffmanNode') -> bool:
        return self.freq < other.freq


def build_tree(data: str) -> HuffmanNode | None:
    """Build a Huffman tree from character frequencies in data."""
    if not data:
        return None
    freq = Counter(data)
    heap = [HuffmanNode(ch, f) for ch, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq, left, right)
        heapq.heappush(heap, merged)

    return heap[0]


def build_codes(node: HuffmanNode | None, prefix: str = '') -> dict[str, str]:
    """Traverse the tree and return {char: binary_code} mapping."""
    if node is None:
        return {}
    if node.char is not None:
        return {node.char: prefix or '0'}
    codes = {}
    codes.update(build_codes(node.left, prefix + '0'))
    codes.update(build_codes(node.right, prefix + '1'))
    return codes


def encode_huffman(data: str) -> tuple[str, dict[str, str]]:
    """Encode data using Huffman coding.

    Returns (bit_string, codebook) where bit_string is the encoded binary
    string and codebook maps each character to its binary code.
    """
    if not data:
        return '', {}
    tree = build_tree(data)
    codes = build_codes(tree)
    return ''.join(codes[ch] for ch in data), codes


def decode_huffman(bits: str, codebook: dict[str, str]) -> str:
    """Decode a Huffman-encoded bit string using the provided codebook."""
    if not bits:
        return ''
    reverse = {v: k for k, v in codebook.items()}
    result = []
    current = ''
    for bit in bits:
        current += bit
        if current in reverse:
            result.append(reverse[current])
            current = ''
    return ''.join(result)
