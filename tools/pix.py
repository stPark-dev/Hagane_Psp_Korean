"""The game's FPIX texture containers: FPIX header, DPIX table, XPIX entries each holding a GIM."""
import struct

from tools import gim


def textures(buf):
    """GIM files in the container, in table order."""
    if buf[:4] != b"FPIX":
        raise ValueError("not an FPIX container")
    dpix, = struct.unpack_from("<I", buf, 0x20)
    if buf[dpix:dpix + 4] != b"DPIX":
        raise ValueError("DPIX table not found")
    n, = struct.unpack_from("<I", buf, dpix + 8)
    out = []
    for off in struct.unpack_from(f"<{n}I", buf, dpix + 0x20):
        x = dpix + off
        if buf[x:x + 4] != b"XPIX":
            raise ValueError(f"entry at {x:#x} is not XPIX")
        size, = struct.unpack_from("<I", buf, x + 4)
        g = buf.index(gim.MAGIC, x, x + size)
        out.append(buf[g:x + size])
    return out
