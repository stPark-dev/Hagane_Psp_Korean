"""Korean encoding and glyph injection for FFON fonts.

The 2,350 KS X 1001 Hangul syllables (25 rows x 94) are assigned to JIS rows
16..40 in the same order, i.e. Shift-JIS 0x889F..0x94FC (the first-level kanji
area). Everything else keeps its Shift-JIS code.
"""
import copy

from tools import ffon

HANGUL_KU_BASE = 16


def _ks_hangul():
    out = []
    for row in range(0xB0, 0xC9):
        for col in range(0xA1, 0xFF):
            out.append(bytes([row, col]).decode("euc-kr"))
    return out


KS_HANGUL = _ks_hangul()
_KUTEN = {ch: (HANGUL_KU_BASE + i // 94, i % 94 + 1) for i, ch in enumerate(KS_HANGUL)}


def hangul_sjis(ch):
    return ffon.kuten_to_sjis(*_KUTEN[ch])


def encode(text):
    out = bytearray()
    for ch in text:
        if ch in _KUTEN:
            out += hangul_sjis(ch).to_bytes(2, "big")
            continue
        try:
            out += ch.encode("cp932")
        except UnicodeEncodeError:
            raise ValueError(f"no code for {ch!r} (U+{ord(ch):04X})") from None
    return bytes(out)


def render_cell(glyph, width, height, baseline, level, x_shift=0):
    """Render a BDF glyph into a 4bpp cell; `baseline` is the cell row the
    glyph's baseline sits on (pixels with yoff 0 end on that row). `x_shift`
    moves the glyph right (negative: left)."""
    row_bytes = (width * 4 + 7) // 8
    cell = bytearray(row_bytes * height)
    top = baseline + 1 - glyph.yoff - glyph.height
    for gy in range(glyph.height):
        y = top + gy
        if not 0 <= y < height:
            continue
        for gx in range(glyph.width):
            x = glyph.xoff + gx + x_shift
            if 0 <= x < width and glyph.pixel(gx, gy):
                cell[y * row_bytes + x // 2] |= level << (4 * (x & 1))
    return bytes(cell)


# Galmuri11-Bold Hangul ink spans columns 0-10; one column right centres it in
# the 14px cell and keeps both edge columns empty (D8-7: no bleed between
# glyphs when the emulator upscales with linear filtering).
HANGUL_X_SHIFT = 1


def add_hangul(font, bdf_font, chars, baseline, level=15, x_shift=0):
    """Return a copy of `font` with glyphs for `chars` appended and their
    assigned codes pointing at them."""
    if font.bpp != 4:
        raise ValueError("only 4bpp fonts are supported")
    out = copy.deepcopy(font)
    for ch in chars:
        g = bdf_font.glyphs.get(ord(ch))
        if g is None:
            raise ValueError(f"BDF font has no glyph for {ch!r}")
        out.glyphs.append(render_cell(g, font.width, font.height, baseline, level, x_shift))
        out.double[_KUTEN[ch]] = len(out.glyphs)
    return out
