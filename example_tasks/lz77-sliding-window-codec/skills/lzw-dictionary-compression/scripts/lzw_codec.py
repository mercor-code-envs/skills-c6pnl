"""LZW dictionary-based compression codec."""


def encode_lzw(data: str) -> list[int]:
    """Compress data using LZW encoding.

    Returns a list of integer codes. The dictionary starts with all 256
    single-byte values and grows dynamically.
    """
    if not data:
        return []

    dict_size = 256
    dictionary: dict[str, int] = {chr(i): i for i in range(dict_size)}

    result: list[int] = []
    w = ""
    for c in data:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        result.append(dictionary[w])
    return result


def decode_lzw(codes: list[int]) -> str:
    """Decompress LZW encoded codes back to original string."""
    if not codes:
        return ""

    dict_size = 256
    dictionary: dict[int, str] = {i: chr(i) for i in range(dict_size)}

    result: list[str] = []
    w = chr(codes[0])
    result.append(w)

    for code in codes[1:]:
        if code in dictionary:
            entry = dictionary[code]
        elif code == dict_size:
            entry = w + w[0]
        else:
            raise ValueError(f"Invalid LZW code: {code}")
        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        w = entry

    return ''.join(result)
