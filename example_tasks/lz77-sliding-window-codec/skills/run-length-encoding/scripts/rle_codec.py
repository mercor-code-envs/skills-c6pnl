"""Run-Length Encoding (RLE) codec."""


def encode_rle(data: str) -> list[tuple[int, str]]:
    """Compress data using run-length encoding.

    Returns a list of (count, char) tuples.
    """
    if not data:
        return []
    result = []
    count = 1
    for i in range(1, len(data)):
        if data[i] == data[i - 1]:
            count += 1
        else:
            result.append((count, data[i - 1]))
            count = 1
    result.append((count, data[-1]))
    return result


def decode_rle(tokens: list[tuple[int, str]]) -> str:
    """Decompress RLE tokens back to original string."""
    return ''.join(ch * count for count, ch in tokens)


def encode_rle_bytes(data: str) -> bytes:
    """Compact binary RLE: each run is 2 bytes (count, ord(char)).

    Count is capped at 255 per run.
    """
    result = bytearray()
    if not data:
        return bytes(result)
    count = 1
    for i in range(1, len(data)):
        if data[i] == data[i - 1] and count < 255:
            count += 1
        else:
            result.extend([count, ord(data[i - 1])])
            count = 1
    result.extend([count, ord(data[-1])])
    return bytes(result)


def decode_rle_bytes(compressed: bytes) -> str:
    """Decompress binary RLE back to string."""
    result = []
    for i in range(0, len(compressed), 2):
        if i + 1 < len(compressed):
            count = compressed[i]
            char = chr(compressed[i + 1])
            result.append(char * count)
    return ''.join(result)
