"""The game's FPIX texture containers: FPIX header, DPIX table, XPIX entries each holding a GIM."""
import struct

from tools import gim


def textures(buf):
    """GIM files in the container, in table order."""
    return [buf[a:b] for a, b in spans(buf)]


def replace(buf, new):
    """Container with textures swapped in place: new = {table index: GIM of the same length}."""
    out = bytearray(buf)
    sp = spans(buf)
    for i, g in new.items():
        a, b = sp[i]
        if len(g) != b - a:
            raise ValueError(f"texture {i}: {len(g)} bytes, slot holds {b - a}")
        out[a:b] = g
    return bytes(out)


def spans(buf):
    """(start, end) of each GIM in the container."""
    if buf[:4] != b"FPIX":
        raise ValueError("not an FPIX container")
    dpix, = struct.unpack_from("<I", buf, 0x20)
    if buf[dpix:dpix + 4] == b"XPIX":  # single texture: no DPIX table (font8_8, route)
        offs = [0]
    elif buf[dpix:dpix + 4] == b"DPIX":
        n, = struct.unpack_from("<I", buf, dpix + 8)
        offs = struct.unpack_from(f"<{n}I", buf, dpix + 0x20)
    else:
        raise ValueError("DPIX table not found")
    out = []
    for off in offs:
        x = dpix + off
        if buf[x:x + 4] != b"XPIX":
            raise ValueError(f"entry at {x:#x} is not XPIX")
        size, = struct.unpack_from("<I", buf, x + 4)
        g = buf.index(gim.MAGIC, x, x + size)
        out.append((g, x + size))
    return out
