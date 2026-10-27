from pathlib import Path

import pytest

from tools import bdf, ffon, kofont

GALMURI = Path(__file__).resolve().parent.parent.parent / "galmuri"

TINY_BDF = """STARTFONT 2.1
FONT tiny
SIZE 4 75 75
FONTBOUNDINGBOX 3 3 0 0
STARTPROPERTIES 2
FONT_ASCENT 3
FONT_DESCENT 0
ENDPROPERTIES
CHARS 1
STARTCHAR U+AC00
ENCODING 44032
SWIDTH 500 0
DWIDTH 4 0
BBX 3 2 1 0
BITMAP
A0
40
ENDCHAR
ENDFONT
"""


def test_bdf_parse():
    f = bdf.parse(TINY_BDF)
    g = f.glyphs[0xAC00]
    assert (g.width, g.height, g.xoff, g.yoff, g.advance) == (3, 2, 1, 0, 4)
    assert g.pixel(0, 0) and not g.pixel(1, 0) and g.pixel(2, 0)
    assert g.pixel(1, 1) and not g.pixel(0, 1)


def test_hangul_code_assignment_follows_ks_x_1001_rows():
    assert kofont.hangul_sjis("가") == ffon.kuten_to_sjis(16, 1)
    assert kofont.hangul_sjis("각") == ffon.kuten_to_sjis(16, 2)
    assert kofont.hangul_sjis("힝") == ffon.kuten_to_sjis(40, 94)
    assert len(kofont.KS_HANGUL) == 2350
    with pytest.raises(KeyError):
        kofont.hangul_sjis("똠")  # not in KS X 1001


def test_encode_mixes_hangul_and_sjis():
    raw = kofont.encode("가 A。@n")
    assert raw == kofont.hangul_sjis("가").to_bytes(2, "big") + " A".encode() + "。".encode("cp932") + b"@n"


def test_encode_rejects_unmapped_character():
    with pytest.raises(ValueError):
        kofont.encode("똠")


def test_render_places_bitmap_on_baseline():
    g = bdf.parse(TINY_BDF).glyphs[0xAC00]
    cell = kofont.render_cell(g, width=4, height=4, baseline=3, level=15)
    # 4bpp, 2 bytes per row, low nibble = left pixel
    px = [[(cell[y * 2 + x // 2] >> (4 * (x & 1))) & 15 for x in range(4)] for y in range(4)]
    assert px[2] == [0, 15, 0, 15]   # glyph row 0 sits at baseline+1-height = 2
    assert px[3] == [0, 0, 15, 0]
    assert px[0] == px[1] == [0, 0, 0, 0]


def test_add_hangul_appends_glyphs_and_remaps_codes():
    base = ffon.Font(width=4, height=4, bpp=4, unknown_size=0, flags=bytes([1, 0]) + bytes(30),
                     single={0x41: 1}, double={(16, 1): 2}, glyphs=[bytes(8), b"\x11" * 8])
    font = bdf.parse(TINY_BDF)
    out = kofont.add_hangul(base, font, "가", baseline=3)
    assert len(out.glyphs) == 3
    assert out.double[(16, 1)] == 3
    assert out.glyphs[2] == kofont.render_cell(font.glyphs[0xAC00], 4, 4, 3, 15)
    assert base.double[(16, 1)] == 2  # input left untouched


@pytest.mark.parametrize("name", ["Galmuri11.bdf", "Galmuri11-Bold.bdf"])
def test_galmuri_covers_ks_hangul(name):
    path = GALMURI / name
    if not path.exists():
        pytest.skip(f"{name} not present")
    f = bdf.parse(path.read_text())
    missing = [c for c in kofont.KS_HANGUL if ord(c) not in f.glyphs]
    assert missing == []


def test_render_shift_moves_glyph_right():
    g = bdf.parse(TINY_BDF).glyphs[0xAC00]
    cell = kofont.render_cell(g, width=4, height=4, baseline=3, level=15, x_shift=-1)
    px = [[(cell[y * 2 + x // 2] >> (4 * (x & 1))) & 15 for x in range(4)] for y in range(4)]
    assert px[2] == [15, 0, 15, 0]
    assert px[3] == [0, 15, 0, 0]


def test_add_hangul_passes_shift():
    base = ffon.Font(width=4, height=4, bpp=4, unknown_size=0, flags=bytes([1, 0]) + bytes(30),
                     single={}, double={(16, 1): 1}, glyphs=[bytes(8)])
    font = bdf.parse(TINY_BDF)
    out = kofont.add_hangul(base, font, "가", baseline=3, x_shift=-1)
    assert out.glyphs[1] == kofont.render_cell(font.glyphs[0xAC00], 4, 4, 3, 15, x_shift=-1)


def test_galmuri_bold_centered_leaves_cell_edges_empty():
    """D8-7: centred Hangul keeps the outer columns of the 14px cell free (no bleed when upscaled)."""
    path = GALMURI / "Galmuri11-Bold.bdf"
    if not path.exists():
        pytest.skip("Galmuri11-Bold.bdf not present")
    f = bdf.parse(path.read_text())
    for c in kofont.KS_HANGUL:
        cell = kofont.render_cell(f.glyphs[ord(c)], 14, 16, 13, 15, x_shift=kofont.HANGUL_X_SHIFT)
        cols = {x for y in range(16) for x in range(14) if (cell[y * 7 + x // 2] >> (4 * (x & 1))) & 15}
        assert 0 not in cols and 13 not in cols, c
