"""FFON bitmap font (FAfont14.fon, cmexFontDefault.fon).

Layout (little endian):
  0x00 'FFON'
  0x04 u32  unknown (not the file size; preserved as-is)
  0x08 u32  1
  0x0C u32  0x100
  0x10 u32  block count
  0x14 u32  number of mapped single-byte codes
  0x18 u32  glyph count
  0x1C u8   width, height, bpp, bytes per glyph row
  0x20 u8   block id of the ASCII block (0x20..0x7E), u8 block id of the
            half-width kana block (0xA0..0xDF) or 0; rest zero
  0x40 u8[96] JIS ku (row) -> block id, 0 = no block
  0xA0 blocks: 96 x u16 glyph index (1-based, 0 = none); for JIS blocks the
       entry index is ten (1..94), for single-byte blocks it is code - base
  then glyph bitmaps, bytes_per_row * height each
"""
import struct
from dataclasses import dataclass, field

HEADER_SIZE = 0xA0
BLOCK_ENTRIES = 96
ASCII_BASE = 0x20
HALF_KANA_BASE = 0xA0


def sjis_to_kuten(code):
    s1, s2 = code >> 8, code & 0xFF
    ku = (s1 - 0x81) * 2 + 1 if s1 <= 0x9F else (s1 - 0xC1) * 2 + 1
    if s2 >= 0x9F:
        return ku + 1, s2 - 0x9E
    return ku, s2 - 0x3F if s2 < 0x7F else s2 - 0x40


def kuten_to_sjis(ku, ten):
    s1 = (ku + 1) // 2 + (0x80 if ku <= 62 else 0xC0)
    if ku % 2 == 0:
        s2 = ten + 0x9E
    else:
        s2 = ten + 0x3F if ten <= 63 else ten + 0x40
    return (s1 << 8) | s2


@dataclass
class Font:
    width: int
    height: int
    bpp: int
    unknown_size: int
    flags: bytes                                  # header bytes 0x20..0x3F
    single: dict = field(default_factory=dict)    # byte code -> glyph index
    double: dict = field(default_factory=dict)    # (ku, ten) -> glyph index
    glyphs: list = field(default_factory=list)    # glyph index i -> glyphs[i - 1]

    @property
    def row_bytes(self):
        return (self.width * self.bpp + 7) // 8

    def glyph_index(self, ch):
        raw = ch.encode("cp932")
        if len(raw) == 1:
            return self.single.get(raw[0])
        return self.double.get(sjis_to_kuten(int.from_bytes(raw, "big")))


def parse(buf):
    if buf[:4] != b"FFON":
        raise ValueError("not an FFON font")
    unknown_size, one, x100, nblocks, nsingle, nglyphs = struct.unpack_from("<6I", buf, 4)
    if (one, x100) != (1, 0x100):
        raise ValueError(f"unexpected FFON header constants {one:#x} {x100:#x}")
    width, height, bpp, row_bytes = buf[0x1C:0x20]
    flags = bytes(buf[0x20:0x40])
    lead = buf[0x40:0xA0]
    f = Font(width, height, bpp, unknown_size, flags)
    if row_bytes != f.row_bytes:
        raise ValueError(f"row bytes {row_bytes} != {f.row_bytes}")

    def block(b):
        return struct.unpack_from(f"<{BLOCK_ENTRIES}H", buf, HEADER_SIZE + (b - 1) * BLOCK_ENTRIES * 2)

    for bid, base in ((flags[0], ASCII_BASE), (flags[1], HALF_KANA_BASE)):
        if bid:
            for i, g in enumerate(block(bid)):
                if g:
                    f.single[base + i] = g
    for ku, bid in enumerate(lead):
        if bid:
            for ten, g in enumerate(block(bid)):
                if g:
                    f.double[(ku, ten)] = g
    if len(f.single) != nsingle:
        raise ValueError(f"single-byte count {len(f.single)} != header {nsingle}")
    gstart = HEADER_SIZE + nblocks * BLOCK_ENTRIES * 2
    gsize = f.row_bytes * height
    if len(buf) != gstart + nglyphs * gsize:
        raise ValueError(f"size {len(buf)} != {gstart + nglyphs * gsize}")
    f.glyphs = [bytes(buf[gstart + i * gsize:gstart + (i + 1) * gsize]) for i in range(nglyphs)]
    return f


def build(f):
    gsize = f.row_bytes * f.height
    for i, g in enumerate(f.glyphs):
        if len(g) != gsize:
            raise ValueError(f"glyph {i + 1} has {len(g)} bytes, expected {gsize}")
    used = set(f.single.values()) | set(f.double.values())
    if used and (min(used) < 1 or max(used) > len(f.glyphs)):
        raise ValueError("glyph index out of range")

    blocks = []
    flags = bytearray(f.flags)
    for slot, base, lo, hi in ((0, ASCII_BASE, 0x20, 0x7F), (1, HALF_KANA_BASE, 0xA0, 0xE0)):
        codes = {c: g for c, g in f.single.items() if lo <= c < hi}
        if codes:
            entries = [0] * BLOCK_ENTRIES
            for c, g in codes.items():
                entries[c - base] = g
            blocks.append(entries)
            flags[slot] = len(blocks)
        else:
            flags[slot] = 0
    if len(f.single) != sum(1 for c in f.single if 0x20 <= c < 0x7F or 0xA0 <= c < 0xE0):
        raise ValueError("single-byte code outside ASCII/half-width kana ranges")
    lead = bytearray(BLOCK_ENTRIES)
    for ku in sorted({k for k, _ in f.double}):
        entries = [0] * BLOCK_ENTRIES
        for (k, ten), g in f.double.items():
            if k == ku:
                entries[ten] = g
        blocks.append(entries)
        lead[ku] = len(blocks)

    out = bytearray(b"FFON")
    out += struct.pack("<6I", f.unknown_size, 1, 0x100, len(blocks), len(f.single), len(f.glyphs))
    out += bytes([f.width, f.height, f.bpp, f.row_bytes])
    out += flags
    out += lead
    for entries in blocks:
        out += struct.pack(f"<{BLOCK_ENTRIES}H", *entries)
    for g in f.glyphs:
        out += g
    return bytes(out)
