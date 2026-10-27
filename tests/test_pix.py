import struct

from tools import pix


def fpix(*gims):
    xs = [b"XPIX" + struct.pack("<I", 0x20 + len(g)) + bytes(0x18) + g for g in gims]
    table_len = 4 * len(xs)
    offs, cur = [], 0x20 + table_len
    for x in xs:
        offs.append(cur); cur += len(x)
    dpix = b"DPIX" + struct.pack("<II", cur, len(xs)) + bytes(0x14) + struct.pack(f"<{len(xs)}I", *offs) + b"".join(xs)
    return b"FPIX" + struct.pack("<I", 0x28 + len(dpix)) + bytes(0x18) + struct.pack("<II", 0x28, len(dpix)) + dpix


def test_textures_returns_each_gim_in_order():
    a, b = b"MIG.00.1PSP\0" + b"A" * 8, b"MIG.00.1PSP\0" + b"B" * 12
    assert pix.textures(fpix(a, b)) == [a, b]


def test_textures_reads_a_single_xpix_without_dpix_table():
    g = b"MIG.00.1PSP\0" + b"C" * 8
    x = b"XPIX" + struct.pack("<I", 0x20 + len(g)) + bytes(0x18) + g
    buf = b"FPIX" + struct.pack("<I", 0x24 + len(x)) + bytes(0x18) + struct.pack("<I", 0x24) + x
    assert pix.textures(buf) == [g]
