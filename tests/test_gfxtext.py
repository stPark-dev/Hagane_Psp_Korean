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


def test_glow_colour_is_the_tint_around_white_text():
    a = np.zeros((20, 40, 4), np.uint8)
    a[5:15, 5:35] = (200, 30, 40, 120)                # red halo
    a[8:12, 10:30] = (255, 255, 255, 255)             # white letters
    assert gfxtext.glow_colour(a, [0, 0, 40, 20]) == (200, 30, 40)


@needs_fonts
def test_logo_edge_sample_draws_white_text_in_the_original_glow():
    pal = struct.pack("<4B", 0, 0, 0, 0) + struct.pack("<4B", 30, 60, 220, 140) + struct.pack("<4B", 255, 255, 255, 255) + bytes(4 * 253)
    idx = bytearray(256 * 256)
    for y in range(10, 40):
        idx[y * 256 + 10:y * 256 + 120] = bytes([1]) * 110
    for y in range(20, 30):
        idx[y * 256 + 20:y * 256 + 110] = bytes([2]) * 90
    t = gim_file(image_block(5, 3, 0, 256, 1, pal), image_block(4, 5, 1, 256, 256, bytes(idx)))
    h = gfxtext.tex_hash(t)
    doc = {"logos": [{"hashes": [h], "erase": [{"box": [0, 0, 128, 48], "mode": "clear"}],
                      "draw": [{"ko": "강철", "box": [0, 0, 128, 48], "px": 30, "edge": "sample", "width": 2, "glow": 1}]}]}
    a = np.frombuffer(gim.decode(gfxtext.redraw(doc, {h: t}, FONTS)[h])[2], np.uint8).reshape(256, 256, 4)
    vis = a[0:48, 0:128][a[0:48, 0:128, 3] > 60]
    assert (vis[:, :3].min(1) > 240).any()            # white letters
    blue = vis[(vis[:, 2] > 150) & (vis[:, 0] < 120)]
    assert len(blue) > 20                              # blue glow, not the default black outline
    assert (vis[:, :3].max(1) < 30).sum() == 0


@needs_fonts
def test_label_cells_spread_one_line_over_separate_cells():
    pal = struct.pack("<4B", 200, 40, 40, 255) + bytes(4 * 255)
    t = gim_file(image_block(5, 3, 0, 256, 1, pal), image_block(4, 5, 1, 256, 256, bytes(256 * 256)))  # opaque red
    h = gfxtext.tex_hash(t)
    cells = [[0, 0, 24, 23], [200, 100, 24, 23], [40, 200, 24, 23]]
    doc = {"labels": [{"hashes": [h], "labels": [{"cells": cells, "ko": "가나다", "style": "popup"}]}]}
    a = np.frombuffer(gim.decode(gfxtext.redraw(doc, {h: t}, FONTS)[h])[2], np.uint8).reshape(256, 256, 4)
    for x, y, w, hh in cells:
        c = a[y:y + hh, x:x + w, 3]
        assert (c == 0).any() and (c == 255).any()   # cleared, then part of the line drawn in each cell
    assert a[60, 100, 3] == 255                        # outside the cells untouched


def test_glow_colour_of_an_untinted_logo_is_its_grey_halo():
    a = np.zeros((20, 40, 4), np.uint8)
    a[5:15, 5:35] = (180, 180, 180, 120)              # white-ish halo, no tint
    a[8:12, 10:30] = (255, 255, 255, 255)
    assert gfxtext.glow_colour(a, [0, 0, 40, 20]) == (180, 180, 180)


def test_glow_colour_of_a_see_through_white_glow_is_the_grey_it_shows_on_black():
    a = np.zeros((20, 40, 4), np.uint8)
    a[5:15, 5:35] = (255, 255, 255, 90)
    assert gfxtext.glow_colour(a, [0, 0, 40, 20]) == (90, 90, 90)


def test_left_aligned_label_keeps_an_inset_free_of_ink():
    a = np.zeros((12, 40, 4), np.uint8)
    gfxtext.draw_label(a, [0, 0, 40, 12], "운", "white", FONTS, "left", inset=2)
    assert not a[:, :2, 3].any() and a[:, 2:, 3].any()


@needs_fonts
def test_label_cells_placed_closer_than_their_width_share_the_overlap():
    pal = struct.pack("<4B", 200, 40, 40, 255) + bytes(4 * 255)
    t = gim_file(image_block(5, 3, 0, 256, 1, pal), image_block(4, 5, 1, 256, 256, bytes(256 * 256)))
    a = np.frombuffer(gim.decode(t)[2], np.uint8).reshape(256, 256, 4).copy()
    cells = [[0, 0, 24, 24], [100, 50, 24, 24], [24, 200, 24, 24]]
    gfxtext.draw_cells(a, cells, "가나다", "popup", FONTS, at=[188, 208, 229])
    c = [a[y:y + h, x:x + w] for x, y, w, h in cells]
    assert (c[0][:, 20:] == c[1][:, :4]).all()          # centres 20 px apart: 4 shared columns
    assert (c[1][:, 21:] == c[2][:, :3]).all()


def test_stat_label_draws_dark_11px_letters_unsqueezed_in_a_12px_cell():
    a = np.zeros((12, 40, 4), np.uint8)
    gfxtext.draw_label(a, [0, 0, 40, 12], "관통", "stat", FONTS, "left", inset=2)
    rows = np.nonzero(a[..., 3].any(1))[0]
    assert rows.max() - rows.min() + 1 == 11                    # full Galmuri11 height, not squeezed
    ink = a[a[..., 3] == 255]
    assert len(ink) and (ink[:, :3] == (37, 34, 31)).all()      # dark, no outline colour


def test_label_anchors_on_the_original_ink_not_the_cell():
    a = np.zeros((12, 80, 4), np.uint8)
    a[2:10, 30:60] = (83, 83, 83, 200)                    # original text sits right of the cell's middle
    gfxtext.draw_label(a, [0, 0, 80, 12], "효과", "grey", FONTS, "center", ink=True)
    xs = np.nonzero(a[..., 3].any(0))[0]
    assert abs((xs.min() + xs.max() + 1) / 2 - 45) <= 1  # centred on the old ink (30..60), not on 40


def test_left_label_starts_where_the_original_ink_started():
    a = np.zeros((12, 80, 4), np.uint8)
    a[2:10, 7:50] = (83, 83, 83, 200)
    gfxtext.draw_label(a, [0, 0, 80, 12], "효과", "grey", FONTS, "left", ink=True)
    assert np.nonzero(a[..., 3].any(0))[0].min() == 7


@needs_fonts
def test_place_label_lines_end_where_the_original_lines_ended():
    a = np.zeros((256, 256, 4), np.uint8)
    a[:, :100] = (90, 90, 90, 255)                       # picture left of the transparent strip
    box = [150, 200, 100, 38]
    a[203:220, 200:250] = (255, 255, 255, 255)          # original name: ends at the box edge (250)
    a[225:234, 220:244] = (255, 255, 255, 255)          # original sub-title: ends 6 px short (244)
    gfxtext.place_label(a, box, "식당", "리올", FONTS)
    ends = [np.nonzero((a[r0:r1, 150:250, 3] > 40).any(0))[0].max() + 151 for r0, r1 in ((200, 223), (223, 238))]
    assert abs(ends[0] - 250) <= 1 and abs(ends[1] - 244) <= 1
