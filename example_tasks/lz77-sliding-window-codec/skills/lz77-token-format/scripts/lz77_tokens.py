"""LZ77 token format utilities: emit and parse 3-byte (offset, length, next_char) tokens."""
import struct

WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15


def emit_token(result: bytearray, offset: int, length: int, next_char: int) -> None:
    """Append a single LZ77 token (3 bytes) to result.

    Args:
        result:    output bytearray being built
        offset:    distance backwards from current position (0 = no match)
        length:    number of matched characters (0 = literal)
        next_char: ord() of the character after the match, or 0 at end of string
    """
    if not (0 <= offset <= 255):
        raise ValueError(f"offset {offset} out of range 0..255")
    if not (0 <= length <= 15):
        raise ValueError(f"length {length} out of range 0..15")
    if not (0 <= next_char <= 255):
        raise ValueError(f"next_char {next_char} out of range 0..255")
    result.extend(struct.pack('BBB', offset, length, next_char))


def read_token(compressed: bytes, i: int) -> tuple[int, int, int]:
    """Read one LZ77 token starting at byte index i.

    Returns:
        (offset, length, next_byte) — all unsigned ints
    """
    if i + 2 >= len(compressed):
        raise IndexError(f"Not enough bytes at position {i}")
    return struct.unpack('BBB', compressed[i:i + 3])


def tokens_from_bytes(compressed: bytes) -> list[tuple[int, int, int]]:
    """Parse all tokens from a compressed byte string.

    Returns list of (offset, length, next_char) tuples.
    """
    if len(compressed) % 3 != 0:
        raise ValueError(f"Compressed length {len(compressed)} is not a multiple of 3")
    return [
        struct.unpack('BBB', compressed[i:i + 3])
        for i in range(0, len(compressed), 3)
    ]


def is_literal_token(offset: int, length: int) -> bool:
    """Return True if this token is a literal (no back-reference)."""
    return offset == 0 and length == 0


def describe_token(offset: int, length: int, next_char: int) -> str:
    """Return a human-readable description of a token."""
    if is_literal_token(offset, length):
        ch = chr(next_char) if next_char != 0 else '\\x00'
        return f"literal({ch!r})"
    else:
        nc = chr(next_char) if next_char != 0 else '<end>'
        return f"backref(offset={offset}, length={length}, next={nc!r})"
