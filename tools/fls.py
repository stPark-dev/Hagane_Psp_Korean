"""FFLS animation files (FLASH/*.fls): the sprites that show parts of the .pix textures.

Only what the graphics-text work needs, read by record shape rather than a full parser:
- bitmap: (id<<16), texture index in the .pix of the same name, (height<<16)|width
- shape: (id<<16)|1, 1, (0x98<<16)|bitmap id, 4 floats box, 4 floats uv (texture pixels)
- placement: (depth<<16)|0xd, object id, matrix a b tx c d ty
"""
import math
import struct

SIZES = (8, 16, 32, 64, 128, 256, 512)


def _words(buf):
    n = len(buf) // 4
    return struct.unpack_from(f"<{n}I", buf), struct.unpack_from(f"<{n}f", buf)


def bitmaps(buf):
    """{bitmap id: texture index}"""
    w, _ = _words(buf)
    return {w[i] >> 16: w[i + 1] for i in range(len(w) - 2)
            if w[i] & 0xffff == 0 and w[i] >> 16 and w[i + 1] < 512
            and w[i + 2] >> 16 in SIZES and w[i + 2] & 0xffff in SIZES}


def shapes(buf):
    """{shape id: (texture index, (x0, y0, x1, y1) uv rect)}"""
    w, f = _words(buf)
    bmp = bitmaps(buf)
    out = {}
    for i in range(3, len(w) - 7):
        if w[i - 3] & 0xffff == 1 and w[i - 1] >> 16 == 0x98 and (w[i - 1] & 0xffff) in bmp:
            u = f[i + 4:i + 8]
            if all(math.isfinite(v) for v in u):
                r = tuple(int(round(v)) for v in (min(u[0], u[2]), min(u[1], u[3]), max(u[0], u[2]), max(u[1], u[3])))
                out[w[i - 3] >> 16] = (bmp[w[i - 1] & 0xffff], r)
    return out


def placements(buf):
    """[(object id, scale a, tx, ty)] for every unrotated placement record"""
    w, f = _words(buf)
    ok = lambda j: math.isfinite(f[j]) and abs(f[j]) < 1e5
    return [(w[i + 1], round(f[i + 2], 2), f[i + 4], f[i + 7]) for i in range(len(w) - 7)
            if w[i] & 0xffff == 0xd and all(ok(j) for j in range(i + 2, i + 8)) and f[i + 3] == 0 and f[i + 5] == 0
            and f[i + 2] > 0]
