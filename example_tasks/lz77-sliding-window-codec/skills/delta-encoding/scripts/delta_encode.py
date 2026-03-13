"""Delta encoding for sequential numeric and string data."""


def encode_delta(values: list[int]) -> list[int]:
    """Encode a list of integers as deltas from successive values.

    The first value is stored as-is; subsequent values store the difference
    from the previous value.
    """
    if not values:
        return []
    result = [values[0]]
    for i in range(1, len(values)):
        result.append(values[i] - values[i - 1])
    return result


def decode_delta(deltas: list[int]) -> list[int]:
    """Decode delta-encoded integers back to original values."""
    if not deltas:
        return []
    result = [deltas[0]]
    for i in range(1, len(deltas)):
        result.append(result[-1] + deltas[i])
    return result


def encode_delta_str(data: str) -> list[int]:
    """Delta-encode a string by operating on character ordinals."""
    return encode_delta([ord(c) for c in data])


def decode_delta_str(deltas: list[int]) -> str:
    """Decode delta-encoded character ordinals back to a string."""
    return ''.join(chr(v) for v in decode_delta(deltas))


def encode_delta_bytes(values: list[int], bits: int = 8) -> bytes:
    """Pack delta-encoded values as signed bytes (deltas clamped to -128..127)."""
    deltas = encode_delta(values)
    result = bytearray()
    # Store first value as 2 bytes (big-endian), then deltas as signed bytes
    first = deltas[0]
    result.extend(first.to_bytes(2, byteorder='big', signed=True))
    for d in deltas[1:]:
        clamped = max(-128, min(127, d))
        result.append(clamped & 0xFF)
    return bytes(result)
