"""Find textures that are mostly black with white text (chapter titles and similar)."""
import sys, json
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
from tools import cpk, pix, gim
idx = json.load(open('work/gfx/sheets/index.json'))
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
cache = {}
def tex(ref):
    p, i = ref.split('#')
    if p not in cache:
        cache.clear(); cache[p] = pix.textures(a.read(P[p]))
    return cache[p][int(i)]
hits = []
for it in idx:
    w, h, rgba = gim.decode(tex(it['first']))
    A = np.frombuffer(rgba, np.uint8).reshape(h, w, 4).astype(int)
    lum = A[..., :3].mean(-1); op = A[..., 3] > 200
    black = ((lum < 20) & op).mean(); white = ((lum > 230) & op).mean()
    if black > 0.45 and 0.03 < white < 0.35:
        hits.append((it, Image.frombytes('RGBA', (w, h), rgba)))
cols, T = 6, 200
W = Image.new('RGB', (cols * T, -(-len(hits) // cols) * (T + 12)), (90, 0, 90)); d = ImageDraw.Draw(W)
for k, (it, im) in enumerate(hits):
    im.thumbnail((T - 2, T - 2)); x, y = (k % cols) * T, (k // cols) * (T + 12)
    W.paste(im, (x + 1, y + 12), im); d.text((x + 1, y), f"{it['n']} x{it['count']}", fill='yellow')
W.save('work/gfx/sheets/titles.png'); print(len(hits))
