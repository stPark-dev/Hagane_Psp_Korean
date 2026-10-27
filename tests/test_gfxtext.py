import os
import struct

import numpy as np
import pytest

from tests.test_gim import gim_file, image_block
from tests.test_pix import fpix
from tools import gfxtext, gim, pix

FONTS = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")
needs_fonts = pytest.mark.skipif(not os.path.exists(os.path.join(FONTS, gfxtext.SERIF)),
                                 reason="Noto Serif KR not in ../fonts (D20)")


def title_gim(seed):
    # white with 16 alpha levels, like the chapter-title atlases
    pal = b"".join(struct.pack("<4B", 255, 255, 255, 17 * k) for k in range(16)) + struct.pack("<4B", 9, 9, 9, 255) + bytes(4 * 239)
    idx = bytes([seed]) * (256 * 256) if seed >= 16 else bytes([seed]) + bytes(256 * 256 - 1)
    return gim_file(image_block(5, 3, 0, 256, 1, pal), image_block(4, 5, 1, 256, 256, idx))


@needs_fonts
def test_patch_redraws_every_copy_and_leaves_other_textures():
    t, other = title_gim(0), title_gim(5)
    doc = {"titles": [{"hashes": [gfxtext.tex_hash(t)], "lines": [{"ko": "두 연금술사"}] + [{"ko": ""}] * 4}]}
    files = {"FLASH/a.pix": fpix(t, other), "FLASH/b.pix": fpix(other, t), "FLASH/c.pix": fpix(other)}
    out = gfxtext.patch(files, doc, FONTS)
    assert set(out) == {"FLASH/a.pix", "FLASH/b.pix"}
    new_a, kept = pix.textures(out["FLASH/a.pix"])
    assert kept == other and pix.textures(out["FLASH/b.pix"]) == [other, new_a]
    a = np.frombuffer(gim.decode(new_a)[2], np.uint8).reshape(256, 256, 4)[..., 3]
    rows = np.where(a.any(1))[0]
    assert 10 <= rows.min() and rows.max() < 48           # text only in the first title row


def test_patch_fails_when_a_texture_is_missing():
    doc = {"titles": [{"hashes": ["000000000000"], "lines": []}]}
    with pytest.raises(ValueError):
        gfxtext.patch({"FLASH/a.pix": fpix(title_gim(0))}, doc, FONTS)


@needs_fonts
def test_redraw_applies_every_section_that_names_a_texture():
    t = title_gim(16)                                 # whole 256x256 texture at palette index 16 (opaque)
    h = gfxtext.tex_hash(t)
    doc = {"labels": [{"hashes": [h], "labels": [{"rect": [0, 0, 32, 12], "ko": "", "style": "black"}]}],
           "logos": [{"hashes": [h], "erase": [{"box": [100, 100, 120, 120], "mode": "clear"}], "draw": []}]}
    a = np.frombuffer(gim.decode(gfxtext.redraw(doc, {h: t}, FONTS)[h])[2], np.uint8).reshape(256, 256, 4)
    assert (a[0:12, 0:32, 3] == 0).all() and (a[100:120, 100:120, 3] == 0).all()
    assert a[50, 50, 3] == 255
