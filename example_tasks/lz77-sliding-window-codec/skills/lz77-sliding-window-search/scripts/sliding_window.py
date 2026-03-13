"""LZ77 sliding window search: longest-match finder and encode/decode reference."""
import struct

WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15


def find_longest_match(data: str, pos: int) -> tuple[int, int]:
    """Find the longest match for data[pos:] in the sliding window.

    Returns (offset, length) where:
      offset = distance backwards from pos to start of match (0 = no match)
      length = number of characters matched (0 = no match)

    Supports overlapping back-references (length > offset).
    """
    n = len(data)
    win_start = max(0, pos - WINDOW_SIZE)
    best_len = 0
    best_off = 0

    for start in range(win_start, pos):
        length = 0
        dist = pos - start
        # Overlapping: modulo wraps the source within the matched segment
        while (length < LOOKAHEAD_SIZE and
               pos + length < n and
               data[start + (length % dist)] == data[pos + length]):
            length += 1

        if length > best_len:
            best_len = length
            best_off = dist

    return best_off, best_len


def encode(data: str) -> bytes:
    """Compress data using LZ77 sliding window.

    Token format: 3 bytes (offset, length, next_char).
    See lz77-token-format skill for full specification.
    """
    result = bytearray()
    pos = 0
    n = len(data)

    while pos < n:
        best_off, best_len = find_longest_match(data, pos)

        if pos + best_len < n:
            next_char = ord(data[pos + best_len])
            advance = best_len + 1
        else:
            next_char = 0
            advance = best_len if best_len > 0 else 1
            if best_len == 0:
                break

        result.extend(struct.pack('BBB', best_off, best_len, next_char))
        pos += advance

    return bytes(result)


def decode(compressed: bytes) -> str:
    """Decompress LZ77 compressed bytes back to original string.

    Copies back-references one character at a time to handle overlapping.
    """
    result = []
    i = 0
    n = len(compressed)

    while i + 2 < n:
        offset, length, next_byte = struct.unpack('BBB', compressed[i:i + 3])
        i += 3

        # Copy back-reference one char at a time (supports offset < length)
        if length > 0:
            start = len(result) - offset
            for j in range(length):
                result.append(result[start + j])

        if next_byte != 0:
            result.append(chr(next_byte))

    return ''.join(result)
