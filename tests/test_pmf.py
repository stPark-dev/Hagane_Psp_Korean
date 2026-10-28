import struct

import pytest

from tools import pmf

HDR = bytes.fromhex("0fd0280100000000")      # frame size ((0x001 + 1) * 8) = 16


def pes(sid, payload):
    return b"\x00\x00\x01" + bytes([sid]) + struct.pack(">H", 3 + len(payload)) + b"\x81\x80\x00" + payload


def stream(frames, cut):
    """PSMF-like file: video and audio packets, audio = HDR+frame units split at the byte offsets in cut."""
    data = b"".join(HDR + f for f in frames)
    out, prev = [], 0
    for c in list(cut) + [len(data)]:
        chunk = data[prev:c]
        # 4-byte header: substream 0, 0, offset of the first unit header that starts in this chunk
        first = next((k - prev for k in range(prev, c) if (k % (8 + len(frames[0]))) == 0), 0xffff)
        out.append(pes(0xbd, b"\x00\x00" + struct.pack(">H", first if first != 0xffff else 0xffff) + chunk))
        out.append(pes(0xe0, b"V" * 7))
        prev = c
    body = b"\x00\x00\x01\xba" + bytes(10) + b"".join(out)
    return b"PSMF0015" + struct.pack(">I", 0x20) + bytes(0x14) + body


def test_audio_frames_reads_the_atrac3plus_units():
    frames = [bytes([k]) * 16 for k in range(5)]
    buf = stream(frames, [30, 61])
    assert pmf.audio_frames(buf) == frames


def test_replace_audio_keeps_packets_and_swaps_every_frame():
    frames = [bytes([k]) * 16 for k in range(5)]
    buf = stream(frames, [30, 61])
    new = [bytes([0x80 + k]) * 16 for k in range(5)]
    out = pmf.replace_audio(buf, new)
    assert len(out) == len(buf) and pmf.audio_frames(out) == new
    assert out.count(b"V" * 7) == buf.count(b"V" * 7)


def test_replace_audio_needs_the_same_count_and_size():
    frames = [bytes([k]) * 16 for k in range(5)]
    buf = stream(frames, [30, 61])
    with pytest.raises(ValueError):
        pmf.replace_audio(buf, frames[:4])
    with pytest.raises(ValueError):
        pmf.replace_audio(buf, [f + b"x" for f in frames])
