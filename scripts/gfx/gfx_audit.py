"""gfx_audit.py: check every redrawn graphics-text area against the sprites (fls shapes) that show it.

For each label / place / logo area in text/ko/graphics.json, the shapes whose uv rect shows the
original ink are the area's frame. Reports
- clip: new ink outside those shapes (cut off on screen), beyond what the original already had there
- bleed: new ink inside other shapes (shows up in another sprite)
- rect: label rects that differ from the shape that shows their ink (snap them to it)
Run from the repository root after scripts/prepare_work.py; needs ../fonts and ../galmuri.
"""
import collections
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from tools import cpk, fls, gfxtext, gim, pix  # noqa: E402

a = cpk.CpkArchive("work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk")
P = a.by_path()
doc = json.load(open("text/ko/graphics.json", encoding="utf-8"))
want = gfxtext.targets(doc)
uv, orig = collections.defaultdict(set), {}
pairs = [(p, p[:-4] + ".fls") for p in P if p.endswith(".pix") and p[:-4] + ".fls" in P]
pairs.append(("FLASH/ID/m_menu.pix", "FLASH/ID/m_menu_pos.fls"))  # the one fls without a .pix of its name
for p, f in pairs:
    texs = pix.textures(a.read(P[p]))
    hs = [gfxtext.tex_hash(g) for g in texs]
    if not want & set(hs):
        continue
    for ti, r in fls.shapes(a.read(P[f])).values():
        if ti < len(hs) and hs[ti] in want:
            uv[hs[ti]].add(r)
            orig.setdefault(hs[ti], texs[ti])
new = gfxtext.redraw(doc, orig, "../fonts")


def arr(g):
    w, h, r = gim.decode(g)
    return np.frombuffer(r, np.uint8).reshape(h, w, 4)


O, N = {h: arr(g) for h, g in orig.items()}, {h: arr(g) for h, g in new.items()}
areas = []
for t in doc["labels"]:
    for lb in t["labels"]:
        boxes = [[x, y, x + w, y + h] for x, y, w, h in (lb["cells"] if "cells" in lb else [lb["rect"]])]
        areas += [(h, f"{lb['ja']}→{lb['ko']}", boxes, lb) for h in t["hashes"]]
for lb in doc["places"]["labels"]:
    x, y, w, h = lb["box"]
    areas.append((lb["hash"], f"place {lb['name']}/{lb['sub']}", [[x, y, x + w, y + h]], None))
for lg in doc["logos"]:
    boxes = [e["box"] for e in lg["erase"]] + [d["box"] for d in lg["draw"]]
    areas += [(h, f"logo {lg['where'][:24]}", boxes, None) for h in lg["hashes"]]


def mask(shape, rects):
    m = np.zeros(shape, bool)
    for x0, y0, x1, y1 in rects:
        m[max(0, y0):y1, max(0, x0):x1] = True
    return m


problems, no_fls = 0, 0
for h, name, boxes, lb in areas:
    if h not in uv:
        no_fls += 1
        continue
    o, n = O[h], N[h]
    A = mask(o.shape[:2], boxes)
    oi, ni = (o[..., 3] > 40) & A, (n[..., 3] > 40) & A
    S = [r for r in uv[h] if oi[max(0, r[1]):r[3], max(0, r[0]):r[2]].any()]
    shown, other = mask(oi.shape, S), mask(oi.shape, [r for r in uv[h] if r not in S])
    clip, lost, bleed = (ni & ~shown).sum(), (oi & ~shown).sum(), (ni & other & ~shown).sum()
    msg = []
    if clip > lost + 2:
        msg.append(f"clip {clip - lost}px")
    if bleed > 2:
        msg.append(f"bleed {bleed}px")
    if lb and "rect" in lb and S:
        x, y, w, hh = lb["rect"]
        best = max(S, key=lambda r: oi[r[1]:r[3], r[0]:r[2]].sum())
        if [best[0], best[1], best[2] - best[0], best[3] - best[1]] != lb["rect"]:
            msg.append(f"rect {lb['rect']} vs shape {list(best)}")
    if msg:
        problems += 1
        print(h, name, "; ".join(msg))
print(f"{len(areas)} areas, {problems} with problems, {no_fls} without an fls of the same name (check on screen)")
