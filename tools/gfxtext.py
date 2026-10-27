"""Korean graphics text (D20): redraw texture text and patch every .pix that holds a copy.

Textures are identified by sha1(GIM bytes)[:12], the hashes used in docs/graphics.md. Each
redrawn texture keeps its GIM layout and palette (gim.remap), so a .pix keeps its size and only
the GIM bytes change. Translations live in text/ko/graphics.json.
"""
import hashlib
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tools import gim, pix

SERIF = "NotoSerifKR-Black.otf"
TITLE_ROW, TITLE_MID, TITLE_SIZE, TITLE_WIDTH = 48, 31, 31, 248  # rows every 48 px, kanji band y 17-44


def tex_hash(g):
    return hashlib.sha1(g).hexdigest()[:12]


def _text_mask(text, font, max_width):
    """Tight 8-bit mask of text, squeezed horizontally to max_width if needed."""
    l, t, r, b = font.getbbox(text)
    m = Image.new("L", (r + 4, b + 4), 0)
    ImageDraw.Draw(m).text((0, 0), text, font=font, fill=255)
    m = m.crop((0, t, r, b))
    if m.width > max_width:
        m = m.resize((max_width, m.height), Image.LANCZOS)
    return m


def title_atlas(lines, fonts_dir, size=TITLE_SIZE):
    """256x256 RGBA: white text, one chapter title per 48-px row, left-aligned like the original."""
    font = ImageFont.truetype(os.path.join(fonts_dir, SERIF), size)
    alpha = Image.new("L", (256, 256), 0)
    for k, text in enumerate(lines):
        if text:
            m = _text_mask(text, font, TITLE_WIDTH)
            alpha.paste(m, (1, TITLE_ROW * k + TITLE_MID - m.height // 2))
    rgba = np.zeros((256, 256, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = np.asarray(alpha)
    return rgba.tobytes()


def redraw(doc, originals, fonts_dir):
    """{hash: new GIM} for every texture in doc that appears in originals ({hash: original GIM})."""
    out = {}
    for t in doc.get("titles", []):
        lines = [x["ko"] for x in t["lines"]]
        for h in t["hashes"]:
            if h in originals:
                out[h] = gim.remap(originals[h], title_atlas(lines, fonts_dir))
    return out


def targets(doc):
    return {h for t in doc.get("titles", []) for h in t["hashes"]}


def patch(pix_files, doc, fonts_dir):
    """{path: new .pix bytes} for the .pix files (given as {path: bytes}) holding a target texture.

    Raises ValueError if a texture named in doc is found nowhere."""
    want = targets(doc)
    found, originals = {}, {}
    for path, buf in pix_files.items():
        for i, g in enumerate(pix.textures(buf)):
            h = tex_hash(g)
            if h in want:
                found.setdefault(path, {})[i] = h
                originals[h] = g
    missing = want - set(originals)
    if missing:
        raise ValueError(f"textures not found: {sorted(missing)}")
    new = redraw(doc, originals, fonts_dir)
    return {p: pix.replace(pix_files[p], {i: new[h] for i, h in slots.items()}) for p, slots in found.items()}
