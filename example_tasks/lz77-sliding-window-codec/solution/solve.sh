#!/usr/bin/env bash
set -euo pipefail
cat > /app/compressor.py << 'PYEOF'
"""sliding window compression codec."""
import struct

WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15


def encode(data: str) -> bytes:
    """Compress a string using LZ77 sliding window compression.

    Each token is 3 bytes: (offset, length, next_char)
      - offset: distance backwards from current position (1..WINDOW_SIZE), 0 if no match
      - length: number of characters in the match (0..LOOKAHEAD_SIZE)
      - next_char: the character immediately after the match (0 if end of string)

    When no match is found: (0, 0, current_char).
    Overlapping back-references are supported: offset < length is valid.
    """
    result = bytearray()
    pos = 0
    n = len(data)

    while pos < n:
        win_start = max(0, pos - WINDOW_SIZE)
        best_len = 0
        best_off = 0

        # Search entire window for the longest match
        for start in range(win_start, pos):
            length = 0
            dist = pos - start  # distance backwards = offset
            # Allow overlapping: data[start + (length % dist)] repeats the match pattern
            while (length < LOOKAHEAD_SIZE and
                   pos + length < n and
                   data[start + (length % dist)] == data[pos + length]):
                length += 1

            if length > best_len:
                best_len = length
                best_off = dist

        # Emit token: next_char is the char after the match
        if pos + best_len < n:
            next_char = ord(data[pos + best_len])
            advance = best_len + 1
        else:
            next_char = 0
            advance = best_len if best_len > 0 else 1
            if best_len == 0:
                # No match and at end — should not happen for non-empty string
                break

        result.extend(struct.pack('BBB', best_off, best_len, next_char))
        pos += advance

    return bytes(result)


def decode(compressed: bytes) -> str:
    """Decompress LZ77 compressed bytes back to the original string.

    Each token is 3 bytes: (offset, length, next_char).
    If offset == 0 and length == 0: emit next_char as a literal.
    Otherwise: copy 'length' chars from (current_pos - offset), then emit next_char.
    Overlapping copies work because we append one character at a time.
    """
    result = []
    i = 0
    n = len(compressed)

    while i + 2 < n:
        offset, length, next_byte = struct.unpack('BBB', compressed[i:i + 3])
        i += 3

        # Copy back-reference (appending one by one supports overlapping)
        if length > 0:
            start = len(result) - offset
            for j in range(length):
                result.append(result[start + j])

        # Emit the literal next character (0 means end-of-string padding)
        if next_byte != 0:
            result.append(chr(next_byte))

    return ''.join(result)
PYEOF
echo "Solution installed at /app/compressor.py"
