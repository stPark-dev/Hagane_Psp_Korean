import struct

from tools import fls


def bitmap(bid, tex, w, h):
    return struct.pack("<3I", bid << 16, tex, (h << 16) | w)


def shape(sid, bid, box, uv):
    return struct.pack("<3I", (sid << 16) | 1, 1, (0x98 << 16) | bid) + struct.pack("<8f", *box, *uv)


def place(depth, oid, tx, ty, a=1.0):
    return struct.pack("<2I", (depth << 16) | 0xd, oid) + struct.pack("<6f", a, 0, tx, 0, a, ty)


def test_shapes_map_uv_rects_to_texture_indexes():
    buf = b"FFLS" + bytes(12) + bitmap(0x19a, 20, 256, 256) + shape(0x19b, 0x19a, (-12, 12, 12, -12), (24, 204, 48, 180))
    assert fls.shapes(buf) == {0x19b: (20, (24, 180, 48, 204))}       # uv normalised to x0 y0 x1 y1


def test_placements_give_final_positions():
    buf = b"FFLS" + bytes(12) + place(7, 0x1a2, 208, 147) + place(6, 0x1a2, 131, 317, 2.9)
    assert fls.placements(buf) == [(0x1a2, 1.0, 208.0, 147.0), (0x1a2, 2.9, 131.0, 317.0)]
