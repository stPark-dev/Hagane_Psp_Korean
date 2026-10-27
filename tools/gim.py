"""Sony GIM textures (inside the game's FPIX/XPIX containers): decode, and re-encode index8 in place.

Block: u16 type, u16 0, u32 size, u32 next, u32 data offset. Types 2 (file)
and 3 (picture) hold child blocks; 4 is the image, 5 the palette. Image and
palette data start with a header: u16 header length, u16 0, u16 format,
u16 order (1 = PSP swizzled), u16 width, u16 height, ..., u32 at 0x1C =
offset of the pixel data.
Formats: 0 RGBA5650, 1 RGBA5551, 2 RGBA4444, 3 RGBA8888, 4 index4, 5 index8.
"""
import struct

import numpy as np

MAGIC = b"MIG.00.1PSP\0"
BITS = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8}


def unswizzle(data, pitch, height):
    """PSP texture swizzle: 16-byte x 8-row blocks stored one after another, row of blocks by row."""
    out = bytearray(pitch * height)
    bw = pitch // 16
    i = 0
    for by in range(0, height, 8):
        for bx in range(bw):
            for y in range(by, min(by + 8, height)):
                o = y * pitch + bx * 16
                out[o:o + 16] = data[i:i + 16]
                i += 16
    return bytes(out)


def swizzle(data, pitch, height):
    """Inverse of unswizzle."""
    out = bytearray(pitch * height)
    bw = pitch // 16
    i = 0
    for by in range(0, height, 8):
        for bx in range(bw):
            for y in range(by, min(by + 8, height)):
                o = y * pitch + bx * 16
                out[i:i + 16] = data[o:o + 16]
                i += 16
    return bytes(out)


def _color(fmt, raw, i):
    if fmt == 3:
        return raw[4 * i:4 * i + 4]
    v, = struct.unpack_from("<H", raw, 2 * i)
    if fmt == 0:
        return bytes([(v & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v >> 11 & 31) * 255 // 31, 255])
    if fmt == 1:
        return bytes([(v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31, 255 if v >> 15 else 0])
    return bytes([(v & 15) * 17, (v >> 4 & 15) * 17, (v >> 8 & 15) * 17, (v >> 12) * 17])


def _leaves(buf, start, end, out):
    pos = start
    while pos + 16 <= end:
        btype, _, size, _, data = struct.unpack_from("<HHIII", buf, pos)
        if size < 16:
            break
        if btype in (2, 3):
            _leaves(buf, pos + data, pos + size, out)
        elif btype in (4, 5):
            out.setdefault(btype, pos + data)
        pos += size
    return out


def _plane(buf, at):
    hdr, _, fmt, order, w, h = struct.unpack_from("<HHHHHH", buf, at)
    start = struct.unpack_from("<I", buf, at + 0x1C)[0] or hdr  # pixel data offset (0x40 in the game files)
    pitch = -(-w * BITS[fmt] // 8 // 16) * 16
    rows = -(-h // 8) * 8 if order else h
    raw = buf[at + start:at + start + pitch * rows]
    if order:
        raw = unswizzle(raw, pitch, rows)
    return fmt, w, h, pitch, raw


def decode(buf):
    """Return (width, height, RGBA bytes)."""
    if not buf.startswith(MAGIC):
        raise ValueError("not a GIM file")
    leaves = _leaves(buf, 16, len(buf), {})
    fmt, w, h, pitch, raw = _plane(buf, leaves[4])
    out = bytearray()
    if fmt in (4, 5):
        pfmt, n, _, _, praw = _plane(buf, leaves[5])
        pal = [_color(pfmt, praw, i) for i in range(n)]
        for y in range(h):
            row = raw[y * pitch:(y + 1) * pitch]
            for x in range(w):
                idx = row[x] if fmt == 5 else (row[x // 2] >> (4 * (x & 1))) & 15
                out += pal[idx]
    else:
        for y in range(h):
            row = raw[y * pitch:(y + 1) * pitch]
            for x in range(w):
                out += _color(fmt, row, x)
    return w, h, bytes(out)


def _index8(buf):
    leaves = _leaves(buf, 16, len(buf), {})
    fmt, w, h, pitch, raw = _plane(buf, leaves[4])
    pfmt, n, _, _, praw = _plane(buf, leaves[5])
    if fmt != 5 or pfmt != 3:
        raise ValueError(f"only index8 + RGBA8888 palette is supported (format {fmt}, palette {pfmt})")
    return leaves, w, h, pitch, raw, np.frombuffer(praw[:4 * n], np.uint8).reshape(n, 4)


def remap(buf, rgba):
    """Same-size GIM with its index8 pixels set to rgba (w*h*4 bytes), keeping the palette.

    Pixels whose colour did not change keep their old index; changed pixels take the nearest
    palette colour (squared RGBA distance), so the palette must already hold the colours drawn."""
    leaves, w, h, pitch, raw, pal = _index8(buf)
    old = np.frombuffer(raw, np.uint8).reshape(-1, pitch)[:h, :w]
    new = np.frombuffer(rgba, np.uint8).reshape(h, w, 4)
    idx = old.copy()
    changed = (pal[old] != new).any(-1)
    if changed.any():
        cols, inv = np.unique(new[changed], axis=0, return_inverse=True)
        d = ((cols[:, None, :].astype(int) - pal[None, :, :].astype(int)) ** 2).sum(-1)
        idx[changed] = d.argmin(1).astype(np.uint8)[inv.ravel()]
    return _write_index8(buf, leaves, idx)


def _write_index8(buf, leaves, idx):
    at = leaves[4]
    _, _, _, order, w, h = struct.unpack_from("<HHHHHH", buf, at)
    start = struct.unpack_from("<I", buf, at + 0x1C)[0] or struct.unpack_from("<H", buf, at)[0]
    pitch = -(-w // 16) * 16
    rows = -(-h // 8) * 8 if order else h
    plane = np.zeros((rows, pitch), np.uint8)
    plane[:h, :w] = idx
    data = plane.tobytes()
    if order:
        data = swizzle(data, pitch, rows)
    out = bytearray(buf)
    out[at + start:at + start + len(data)] = data
    return bytes(out)
