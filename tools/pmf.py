"""PSMF movies (.pmf): read and swap the ATRAC3plus audio without touching the packet layout.

The audio is private stream 1 (0xBD). Each PES payload starts with a 4-byte header (substream,
0, offset of the first audio unit that starts in it); the payloads joined are a run of units of
an 8-byte header (0F D0, 2 config bytes, 4 zero bytes) followed by one ATRAC3plus frame whose size
is ((config & 0x3ff) + 1) * 8 bytes.
"""
import struct


def _audio_regions(buf):
    """[(offset, length)] of the audio bytes in each 0xBD packet, after its 4-byte header."""
    i, out = struct.unpack_from(">I", buf, 8)[0], []
    while i + 6 <= len(buf):
        if buf[i:i + 3] != b"\x00\x00\x01":
            i += 1
            continue
        sid = buf[i + 3]
        if sid == 0xB9:
            break
        if sid == 0xBA:
            i += 14 + (buf[i + 13] & 7)
            continue
        length = struct.unpack_from(">H", buf, i + 4)[0]
        if sid == 0xBD:
            start = i + 9 + buf[i + 8] + 4
            out.append((start, i + 6 + length - start))
        i += 6 + length
    return out


def _units(buf):
    regions = _audio_regions(buf)
    data = b"".join(buf[o:o + n] for o, n in regions)
    if data[:2] != b"\x0f\xd0":
        raise ValueError("audio does not start with an ATRAC3plus unit header")
    size = ((struct.unpack_from(">H", data, 2)[0] & 0x3FF) + 1) * 8
    if len(data) % (8 + size):
        raise ValueError(f"audio length {len(data)} is not a whole number of {8 + size}-byte units")
    return regions, data, size


def audio_frames(buf):
    """The ATRAC3plus frames, without their 8-byte unit headers."""
    _, data, size = _units(buf)
    u = 8 + size
    return [data[k + 8:k + u] for k in range(0, len(data), u)]


def replace_audio(buf, frames):
    """buf with every ATRAC3plus frame replaced by frames (same count and size); headers, packets
    and video stay byte for byte."""
    regions, data, size = _units(buf)
    u = 8 + size
    if len(frames) != len(data) // u or any(len(f) != size for f in frames):
        raise ValueError(f"need {len(data) // u} frames of {size} bytes")
    new = bytearray(data)
    for k, f in enumerate(frames):
        new[k * u + 8:(k + 1) * u] = f
    out, pos = bytearray(buf), 0
    for o, n in regions:
        out[o:o + n] = new[pos:pos + n]
        pos += n
    return bytes(out)
