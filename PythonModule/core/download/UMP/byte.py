def _read_varint(data: bytes, pos: int):
    value = 0
    shift = 0

    while True:
        b = data[pos]
        pos += 1

        value |= (b & 0x7F) << shift

        if not b & 0x80:
            return value, pos

        shift += 7


def _write_varint(value: int) -> bytes:
    out = bytearray()

    while True:
        b = value & 0x7F
        value >>= 7

        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)