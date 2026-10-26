from pathlib import Path

import pytest

from tools import ffon

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "work/iso/PSP_GAME/USRDIR/DATA"


def test_sjis_jis_conversion():
    assert ffon.sjis_to_kuten(0x82A0) == (4, 2)      # あ
    assert ffon.sjis_to_kuten(0x8140) == (1, 1)      # full-width space
    assert ffon.sjis_to_kuten(0x889F) == (16, 1)     # 亜
    assert ffon.sjis_to_kuten(0x9FFC) == (62, 94)
    assert ffon.sjis_to_kuten(0xE040) == (63, 1)
    for ku in range(1, 95):
        for ten in range(1, 95):
            assert ffon.sjis_to_kuten(ffon.kuten_to_sjis(ku, ten)) == (ku, ten)


def _tiny_font():
    f = ffon.Font(width=4, height=2, bpp=4, unknown_size=0, flags=bytes(32),
                  single={0x41: 1}, double={(4, 2): 2}, glyphs=[bytes(4), b"\x11" * 4])
    f.flags = bytes([1, 0]) + bytes(30)
    return f


def test_build_parse_roundtrip_synthetic():
    f = _tiny_font()
    g = ffon.parse(ffon.build(f))
    assert g.single == {0x41: 1}
    assert g.double == {(4, 2): 2}
    assert g.glyphs == f.glyphs
    assert (g.width, g.height, g.bpp) == (4, 2, 4)


def test_glyph_for_sjis_text():
    g = ffon.parse(ffon.build(_tiny_font()))
    assert g.glyph_index("A") == 1
    assert g.glyph_index("あ") == 2
    assert g.glyph_index("い") is None


@pytest.mark.parametrize("name", ["FAfont14.fon", "cmexFontDefault.fon"])
def test_real_font_roundtrip_is_byte_identical(name):
    p = DATA / name
    if not p.exists():
        pytest.skip("extracted disc not present")
    raw = p.read_bytes()
    f = ffon.parse(raw)
    assert ffon.build(f) == raw


def test_fafont14_shape():
    p = DATA / "FAfont14.fon"
    if not p.exists():
        pytest.skip("extracted disc not present")
    f = ffon.parse(p.read_bytes())
    assert (f.width, f.height, f.bpp) == (14, 16, 4)
    assert len(f.glyphs) == 2144
    assert f.glyph_index("エ") and f.glyph_index("錬") and f.glyph_index("A")
