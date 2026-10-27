import struct

from tools import gim


def block(btype, payload, children=b""):
    size = 0x10 + len(payload) + len(children)
    return struct.pack("<HHIII", btype, 0, size, 0x10 + len(payload) + len(children) if not children else 0x10, 0x10) + payload + children


def image_block(btype, fmt, order, w, h, pixels):
    hdr = struct.pack("<HHHHHHHH", 0x30, 0, fmt, order, w, h, 32, 16) + bytes(0x30 - 16)
    data = hdr + pixels
    return struct.pack("<HHIII", btype, 0, 0x10 + len(data), 0x10 + len(data), 0x10) + data


def gim_file(*blocks):
    pic = b"".join(blocks)
    picture = struct.pack("<HHIII", 3, 0, 0x10 + len(pic), 0x10 + len(pic), 0x10) + pic
    root = struct.pack("<HHIII", 2, 0, 0x10 + len(picture), 0x10 + len(picture), 0x10) + picture
    return b"MIG.00.1PSP\0" + bytes(4) + root


def test_unswizzle_restores_row_order():
    # 32x8 bytes: two 16-byte-wide blocks of 8 rows, stored block after block
    linear = bytes(range(256))
    swz = bytearray()
    for bx in range(2):
        for y in range(8):
            swz += linear[y * 32 + bx * 16: y * 32 + bx * 16 + 16]
    assert gim.unswizzle(bytes(swz), 32, 8) == linear


def test_decode_rgba8888_linear():
    px = bytes([255, 0, 0, 255, 0, 255, 0, 255])
    w, h, rgba = gim.decode(gim_file(image_block(4, 3, 0, 2, 1, px)))
    assert (w, h, rgba) == (2, 1, px)


def test_decode_index8_with_palette():
    pal = struct.pack("<4B", 0, 0, 0, 255) + struct.pack("<4B", 10, 20, 30, 255) + bytes(4 * 254)
    w, h, rgba = gim.decode(gim_file(image_block(5, 3, 0, 256, 1, pal), image_block(4, 5, 0, 2, 1, bytes([1, 0]))))
    assert rgba == bytes([10, 20, 30, 255, 0, 0, 0, 255])


def test_decode_index4_low_nibble_first():
    pal = struct.pack("<4B", 0, 0, 0, 255) + struct.pack("<4B", 9, 9, 9, 255) + bytes(4 * 14)
    w, h, rgba = gim.decode(gim_file(image_block(5, 3, 0, 16, 1, pal), image_block(4, 4, 0, 2, 1, bytes([0x01]))))
    assert rgba == bytes([9, 9, 9, 255, 0, 0, 0, 255])


def test_pixel_data_offset_comes_from_the_header_when_set():
    hdr = bytearray(struct.pack("<HHHHHHHH", 0x30, 0, 3, 0, 1, 1, 32, 16) + bytes(0x30 - 16))
    struct.pack_into("<I", hdr, 0x1C, 0x40)
    data = bytes(hdr) + bytes(0x10) + bytes([1, 2, 3, 4])  # 16 filler bytes, pixels at 0x40
    img = struct.pack("<HHIII", 4, 0, 0x10 + len(data), 0x10 + len(data), 0x10) + data
    assert gim.decode(gim_file(img)) == (1, 1, bytes([1, 2, 3, 4]))
