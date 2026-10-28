"""Korean graphics text (D20): redraw texture text and patch every .pix that holds a copy.

Textures are identified by sha1(GIM bytes)[:12], the hashes used in docs/graphics.md. Each
redrawn texture keeps its GIM layout and palette (gim.remap), so a .pix keeps its size and only
the GIM bytes change. Translations live in text/ko/graphics.json.
"""
import hashlib
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from tools import bdf, gim, pix

SERIF, SANS = "NotoSerifKR-Black.otf", "NotoSansKR-Black.otf"
BOLD, SMALL, TINY = "galmuri/Galmuri11-Bold.bdf", "galmuri/Galmuri9.bdf", "galmuri/Galmuri7.bdf"
# Label styles, sampled from the original atlases. fill: one colour or a top-to-bottom gradient
# ("sample" = take the gradient from the original pixels); alpha: plain styles only (anti-aliased
# coverage); edge: outline colour and width; shadow: colour drawn one pixel down-right of the edge;
# fonts: bitmap fonts tried in order, or ("sans", px) for the vector font.
STYLES = {
    "black": {"fill": (0, 0, 0), "alpha": 190, "fonts": (SMALL,)},
    "grey": {"fill": (83, 83, 83), "alpha": 200, "fonts": (SMALL,)},
    "grey_tiny": {"fill": (83, 83, 83), "alpha": 200, "fonts": (TINY,)},
    "blue": {"fill": (0, 120, 254), "alpha": 255, "fonts": (BOLD, SMALL)},
    "green": {"fill": [(0, 255, 113), (1, 228, 101), (0, 186, 83), (1, 121, 54)],
              "edge": ((2, 10, 6, 255), 1), "fonts": (BOLD, SMALL)},
    "white": {"fill": [(255, 255, 255), (255, 255, 255), (237, 236, 235), (187, 186, 189)],
              "edge": ((37, 34, 31, 255), 1), "shadow": (0, 0, 0, 125), "fonts": (SMALL,)},
    "bond": {"fill": "sample", "edge": ((255, 255, 255, 255), 2), "fonts": ("sans", 15)},
    "popup": {"fill": "sample", "edge": ((24, 16, 10, 255), 2), "fonts": ("sans", 20)},
    "chain": {"fill": [(255, 236, 90), (255, 196, 50), (255, 150, 30), (235, 100, 20)],
              "edge": ((20, 70, 210, 255), 1), "fonts": ("sans", 16)},
    "chain_small": {"fill": [(255, 236, 90), (255, 196, 50), (255, 150, 30), (235, 100, 20)],
                    "edge": ((20, 70, 210, 255), 1), "fonts": ("sans", 14)},
}
_bdf = {}


def _bitmap_font(fonts_dir, name):
    # Galmuri sits next to the fonts folder (../galmuri, as for the dialogue font)
    path = os.path.normpath(os.path.join(fonts_dir, "..", name))
    if path not in _bdf:
        _bdf[path] = bdf.parse(open(path, encoding="utf-8").read())
    return _bdf[path]


def bitmap_mask(font, text):
    """0/1 array of text in a BDF font, cropped to the inked rows and columns."""
    width = sum(font.glyphs[ord(c)].advance for c in text)
    h = font.ascent + font.descent
    m = np.zeros((h, max(width, 1)), np.uint8)
    x = 0
    for c in text:
        g = font.glyphs[ord(c)]
        top = font.ascent - g.yoff - g.height
        for y in range(g.height):
            for gx in range(g.width):
                if g.pixel(gx, y):
                    m[top + y, x + g.xoff + gx] = 1
        x += g.advance
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else m[:0, :0]


def fit_bitmap(text, fonts_dir, max_w, max_h, fonts):
    """Coverage (float 0-1) of text in the first bitmap font that fits, squeezed if none does."""
    for name in fonts:
        m = bitmap_mask(_bitmap_font(fonts_dir, name), text)
        if m.shape[1] <= max_w and m.shape[0] <= max_h:
            return m.astype(float)
    img = Image.fromarray(m * 255).resize((max_w, min(m.shape[0], max_h)), Image.LANCZOS)
    return np.asarray(img, float) / 255


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


def _vector_mask(text, fonts_dir, px):
    font = ImageFont.truetype(os.path.join(fonts_dir, SANS), px)
    l, t, r, bt = font.getbbox(text)
    m = Image.new("L", (r + 4, bt + 4), 0)
    ImageDraw.Draw(m).text((0, 0), text, font=font, fill=255)
    return np.asarray(m.crop((l, t, r, bt)), float) / 255


def _coverage(text, fonts_dir, w, h, fonts):
    if fonts[0] == "sans":
        cov = _vector_mask(text, fonts_dir, fonts[1])
        if cov.shape[1] > w or cov.shape[0] > h:
            img = Image.fromarray((cov * 255).astype(np.uint8))
            cov = np.asarray(img.resize((min(cov.shape[1], w), min(cov.shape[0], h)), Image.LANCZOS), float) / 255
        return cov
    return fit_bitmap(text, fonts_dir, w, h, fonts)


def _dilate(on, n):
    out = on.copy()
    for _ in range(n):
        grown = out.copy()
        grown[1:] |= out[:-1]; grown[:-1] |= out[1:]
        grown[:, 1:] |= out[:, :-1]; grown[:, :-1] |= out[:, 1:]
        grown[1:, 1:] |= out[:-1, :-1]; grown[:-1, :-1] |= out[1:, 1:]
        grown[1:, :-1] |= out[:-1, 1:]; grown[:-1, 1:] |= out[1:, :-1]
        out = grown
    return out


def _sample_gradient(rgba, rect, n=4):
    """Top-to-bottom fill colours of the original text in rect: mean of saturated pixels per band."""
    x, y, w, h = rect
    a = rgba[y:y + h, x:x + w].astype(int)
    sat = (a[..., :3].max(-1) - a[..., :3].min(-1) > 60) & (a[..., 3] > 200)
    rows = np.where(sat.any(1))[0]
    out = []
    for band in np.array_split(rows, n):
        px = a[band][sat[band]]
        out.append(tuple(int(v) for v in px[:, :3].mean(0)))
    return out


def draw_label(rgba, rect, text, style, fonts_dir, align="center", inset=0):
    """Clear rect in rgba (h, w, 4 array) and draw text in it (align: center, left or right), in one of STYLES.
    inset keeps that many columns at the left free (the game's sprite of the label before may reach into them)."""
    st = STYLES[style]
    x, y, w, h = rect
    fill = _sample_gradient(rgba, rect) if st["fill"] == "sample" else st["fill"]
    rgba[y:y + h, x:x + w] = 0
    if not text:
        return
    edge, ew = st.get("edge", (None, 0))
    sh = 1 if "shadow" in st else 0
    cov = _coverage(text, fonts_dir, w - 2 * ew - sh - inset, h - 2 * ew - sh, st["fonts"])
    ch, cw = cov.shape
    ox, oy = x + (w - cw - sh) // 2, y + (h - ch - sh) // 2
    if align == "left":
        ox = x + ew + inset
    elif align == "right":
        ox = x + w - ew - sh - cw
    if edge is None:
        region = rgba[oy:oy + ch, ox:ox + cw]
        a = (cov * st["alpha"]).astype(np.uint8)
        region[a > 0] = tuple(fill) + (0,)
        region[..., 3] = np.maximum(region[..., 3], a)
        return
    on = np.zeros((ch + 2 * ew + sh, cw + 2 * ew + sh), bool)
    on[ew:ew + ch, ew:ew + cw] = cov > 0.5
    outline = _dilate(on, ew)
    region = rgba[oy - ew:oy - ew + on.shape[0], ox - ew:ox - ew + on.shape[1]]
    if sh:
        shadow = np.zeros_like(outline)
        shadow[1:, 1:] = outline[:-1, :-1]
        region[shadow & ~outline] = st["shadow"]
    region[outline] = edge
    grad = [fill] if isinstance(fill[0], int) else fill
    for r in range(ch):
        row = region[ew + r]
        row[on[ew + r]] = tuple(grad[min(r * len(grad) // ch, len(grad) - 1)]) + (255,)


def draw_cells(rgba, cells, text, style, fonts_dir, at=None):
    """Draw one line of text across cells ([x, y, w, h] each, same size) that the game shows in this
    order, like the battle pop-ups built from one-glyph tiles. at: screen x of each cell's centre
    (cells may overlap there); default side by side."""
    w, h = cells[0][2], cells[0][3]
    at = at or [w // 2 + w * k for k in range(len(cells))]
    left = min(at) - w // 2
    strip = np.zeros((h, max(at) - left + w - w // 2, 4), np.uint8)
    for (x, y, _, _), c in zip(cells, at):                  # original colours, for the sampled fill
        strip[:, c - w // 2 - left:c - w // 2 - left + w] = rgba[y:y + h, x:x + w]
    draw_label(strip, [0, 0, strip.shape[1], h], text, style, fonts_dir)
    for (x, y, _, _), c in zip(cells, at):
        rgba[y:y + h, x:x + w] = strip[:, c - w // 2 - left:c - w // 2 - left + w]


PLACE_NAME_PX, PLACE_SUB_PX, PLACE_NAME_ROWS = 20, 12, 23  # name band = first 23 rows of the box


def _outlined(text, fonts_dir, px, edge, max_w):
    """(alpha of white outline, alpha of black text) for text, squeezed to max_w if wider."""
    t = _vector_mask(text, fonts_dir, px)
    if t.shape[1] + 2 * edge > max_w:
        img = Image.fromarray((t * 255).astype(np.uint8))
        t = np.asarray(img.resize((max_w - 2 * edge, t.shape[0]), Image.LANCZOS), float) / 255
    t = np.pad(t, edge)
    o = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * edge + 1)), float) / 255
    return o, t


def place_label(rgba, box, name, sub, fonts_dir):
    """Redraw a location label: black serif text with a white outline, right-aligned in box,
    name on top and the smaller sub-title under it. The label sits on the transparent strip
    (alpha <= 2) at the bottom of a background tile, right of the picture."""
    x, y, w, h = box
    left = rgba.shape[1]
    firsts = {r: np.nonzero(rgba[r, :, 3] <= 2)[0] for r in range(y, y + h)}
    strip = int(np.median([z[0] for z in firsts.values() if len(z)]))
    for r, z in firsts.items():
        if len(z):
            start = min(z[0], x, strip)            # a glyph touching the picture hides the strip edge
            rgba[r, start:] = 0                    # the strip right of the picture holds only the label
            left = min(left, start + 2)
    right = x + w
    for text, px, top, rows, edge in ((name, PLACE_NAME_PX, y, PLACE_NAME_ROWS, 2),
                                      (sub, PLACE_SUB_PX, y + PLACE_NAME_ROWS, h - PLACE_NAME_ROWS, 1)):
        if not text:
            continue
        o, t = _outlined(text, fonts_dir, px, edge, right - left)
        oy = top + (rows - o.shape[0]) // 2
        ox = right - o.shape[1]
        region = rgba[oy:oy + o.shape[0], ox:ox + o.shape[1]].astype(float)
        a_new = np.maximum(o, t)
        rgb = 255 * (1 - t[..., None])                      # white outline, black text over it
        base_a = region[..., 3:] / 255
        a_out = a_new[..., None] + base_a * (1 - a_new[..., None])
        mix = (rgb * a_new[..., None] + region[..., :3] * base_a * (1 - a_new[..., None])) / np.maximum(a_out, 1e-6)
        region[..., :3] = mix
        region[..., 3:] = a_out * 255
        rgba[oy:oy + o.shape[0], ox:ox + o.shape[1]] = np.clip(region + 0.5, 0, 255).astype(np.uint8)


def erase(rgba, box, mode, thr=110):
    """Remove text inside box = [x0, y0, x1, y1]: "clear" makes every visible pixel transparent,
    "inpaint" fills the pixels brighter than thr from their surroundings (text drawn over a picture),
    "inpaint_dark" the pixels darker than thr and the light outline around them."""
    x0, y0, x1, y1 = box
    sub = rgba[y0:y1, x0:x1]
    if mode == "clear":
        sub[sub[..., 3] > 20] = 0
        return
    import cv2
    lum = sub[..., :3].astype(int).mean(-1)
    m = (((lum < thr) if mode == "inpaint_dark" else (lum > thr)) & (sub[..., 3] > 20)).astype(np.uint8) * 255
    if mode == "inpaint_dark":                      # and the light outline right around the letters
        m |= ((lum > 200) & (cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0)).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    sub[..., :3] = cv2.inpaint(np.ascontiguousarray(sub[..., :3]), m, 4, cv2.INPAINT_TELEA)
    sub[..., 3] = cv2.inpaint(np.ascontiguousarray(sub[..., 3]), m, 4, cv2.INPAINT_TELEA)


def glow_colour(rgba, box):
    """Mean colour of the tinted (not white, visible) pixels in box = [x0, y0, x1, y1]: the glow
    around white logo letters."""
    x0, y0, x1, y1 = box
    p = rgba[y0:y1, x0:x1].reshape(-1, 4).astype(int)
    p = p[p[:, 3] > 30]
    tinted = p[p[:, :3].max(1) - p[:, :3].min(1) > 40]
    grey = p[p[:, :3].min(1) < 240]
    if len(tinted) or len(grey):
        halo = tinted if len(tinted) else grey
        return tuple(int(round(v)) for v in halo[:, :3].mean(0))
    # a see-through white glow: the grey it shows over the dark loading screen
    return tuple(int(round(v)) for v in (p[:, :3] * p[:, 3:] / 255).mean(0))


def draw_text(rgba, text, box, px, fonts_dir, fill=(255, 255, 255), edge=(0, 0, 0), width=1, spacing=0, glow=0):
    """Text centred in box = [x0, y0, x1, y1], in Noto Serif KR, with an outline; squeezed to fit.
    glow > 0 blurs the outline by that radius (a soft halo instead of a hard edge).

    The box may run past the texture edge (text cut there, like the original)."""
    pad = 64
    big = np.zeros((rgba.shape[0] + 2 * pad, rgba.shape[1] + 2 * pad, 4), np.uint8)
    big[pad:-pad, pad:-pad] = rgba
    _draw_text(big, text, [v + pad for v in box], px, fonts_dir, fill, edge, width, spacing, glow)
    rgba[:] = big[pad:-pad, pad:-pad]


def _draw_text(rgba, text, box, px, fonts_dir, fill, edge, width, spacing, glow=0):
    x0, y0, x1, y1 = box
    font = ImageFont.truetype(os.path.join(fonts_dir, SERIF), px)
    advances = [font.getlength(c) for c in text]
    m = Image.new("L", (int(sum(advances) + spacing * len(text)) + 8, 2 * px), 0)
    d, x = ImageDraw.Draw(m), 2
    for c, adv in zip(text, advances):
        d.text((x, 0), c, font=font, fill=255)
        x += adv + spacing
    m = m.crop(m.getbbox())
    m = m.resize((min(m.width, x1 - x0 - 2 * width), min(m.height, y1 - y0 - 2 * width)), Image.LANCZOS)
    m = Image.fromarray(np.pad(np.asarray(m), width + glow))
    t = np.asarray(m, float) / 255
    o = m.filter(ImageFilter.MaxFilter(2 * width + 1))
    if glow:
        o = o.filter(ImageFilter.GaussianBlur(glow))
    o = np.asarray(o, float) / 255
    ox, oy = x0 + (x1 - x0 - m.width) // 2, y0 + (y1 - y0 - m.height) // 2
    region = rgba[oy:oy + m.height, ox:ox + m.width].astype(float)
    for a, col in ((o, edge), (t, fill)):                    # outline first, then the letters over it
        a = a[..., None]
        base = region[..., 3:] / 255
        out = a + base * (1 - a)
        region[..., :3] = (np.array(col) * a + region[..., :3] * base * (1 - a)) / np.maximum(out, 1e-6)
        region[..., 3:] = out * 255
    rgba[oy:oy + m.height, ox:ox + m.width] = np.clip(region + 0.5, 0, 255).astype(np.uint8)


def redraw(doc, originals, fonts_dir):
    """{hash: new GIM} for every texture in doc that appears in originals ({hash: original GIM}).

    A texture named in several sections gets all their changes, in the order titles, labels,
    places, logos, and is encoded once."""
    work = {}

    def canvas(h):
        if h not in work:
            w, hh, rgba = gim.decode(originals[h])
            work[h] = np.frombuffer(rgba, np.uint8).reshape(hh, w, 4).copy()
        return work[h]

    for t in doc.get("titles", []):
        lines = [x["ko"] for x in t["lines"]]
        for h in t["hashes"]:
            if h in originals:
                work[h] = np.frombuffer(title_atlas(lines, fonts_dir), np.uint8).reshape(256, 256, 4).copy()
    for t in doc.get("labels", []):
        for h in t["hashes"]:
            if h in originals:
                a = canvas(h)
                for lb in t["labels"]:
                    if "cells" in lb:
                        draw_cells(a, lb["cells"], lb["ko"], lb["style"], fonts_dir, lb.get("at"))
                    else:
                        draw_label(a, lb["rect"], lb["ko"], lb["style"], fonts_dir, lb.get("align", "center"),
                                   lb.get("inset", 0))
    places = doc.get("places", {})
    for lb in places.get("labels", []):
        if lb["hash"] in originals:
            terms = places["terms"]
            place_label(canvas(lb["hash"]), lb["box"], terms[lb["name"]], terms[lb["sub"]], fonts_dir)
    for lg in doc.get("logos", []):
        for h in lg["hashes"]:
            if h in originals:
                a = canvas(h)
                # "edge": "sample" takes the glow colour of the original letters before they are erased
                edges = [glow_colour(a, t["box"]) if t.get("edge") == "sample" else t.get("edge", (0, 0, 0))
                         for t in lg["draw"]]
                for e in lg["erase"]:
                    erase(a, e["box"], e["mode"], e.get("thr", 110))
                for t, edge in zip(lg["draw"], edges):
                    draw_text(a, t["ko"], t["box"], t["px"], fonts_dir, t.get("fill", (255, 255, 255)),
                              edge, t.get("width", 1), t.get("spacing", 0), t.get("glow", 0))
    return {h: gim.remap(originals[h], a.tobytes()) for h, a in work.items()}


def targets(doc):
    hashes = {h for key in ("titles", "labels", "logos") for t in doc.get(key, []) for h in t["hashes"]}
    return hashes | {lb["hash"] for lb in doc.get("places", {}).get("labels", [])}


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
