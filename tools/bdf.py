"""Minimal BDF bitmap font reader."""
from dataclasses import dataclass


@dataclass
class Glyph:
    width: int
    height: int
    xoff: int
    yoff: int
    advance: int
    rows: list   # ints, MSB = leftmost pixel, padded to whole bytes
    row_bits: int

    def pixel(self, x, y):
        return bool((self.rows[y] >> (self.row_bits - 1 - x)) & 1)


@dataclass
class Font:
    ascent: int
    descent: int
    glyphs: dict  # codepoint -> Glyph


def parse(text):
    ascent = descent = 0
    glyphs = {}
    lines = iter(text.splitlines())
    for line in lines:
        key, _, rest = line.partition(" ")
        if key == "FONT_ASCENT":
            ascent = int(rest)
        elif key == "FONT_DESCENT":
            descent = int(rest)
        elif key == "STARTCHAR":
            enc = adv = None
            bbx = None
            for line in lines:
                key, _, rest = line.partition(" ")
                if key == "ENCODING":
                    enc = int(rest.split()[0])
                elif key == "DWIDTH":
                    adv = int(rest.split()[0])
                elif key == "BBX":
                    bbx = [int(v) for v in rest.split()]
                elif key == "BITMAP":
                    w, h, xo, yo = bbx
                    rows = [int(next(lines).strip() or "0", 16) for _ in range(h)]
                    bits = ((w + 7) // 8) * 8
                    if enc is not None and enc >= 0:
                        glyphs[enc] = Glyph(w, h, xo, yo, adv, rows, bits)
                elif key == "ENDCHAR":
                    break
    return Font(ascent, descent, glyphs)
