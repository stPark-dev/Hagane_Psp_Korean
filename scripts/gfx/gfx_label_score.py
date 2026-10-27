"""Score each unique 2D texture for an outlined white label in its lower-right corner."""
import sys, json
sys.path.insert(0, '.')
import numpy as np
from tools import cpk, pix, gim
idx = json.load(open('work/gfx/sheets/index.json'))
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
cache = {}
def tex(ref):
    p, i = ref.split('#')
    if p not in cache:
        cache.clear(); cache[p] = pix.textures(a.read(P[p]))
    return cache[p][int(i)]
out = []
for it in idx:
    w, h, rgba = gim.decode(tex(it['first']))
    A = np.frombuffer(rgba, np.uint8).reshape(h, w, 4).astype(int)
    r = A[int(h * 0.80):, int(w * 0.45):]
    lum = r[..., :3].mean(-1); op = r[..., 3] > 200
    white = (lum > 225) & op; black = (lum < 40) & op
    # white pixels with a black neighbour (outlined glyph strokes)
    wb = white & (np.roll(black, 1, 0) | np.roll(black, -1, 0) | np.roll(black, 1, 1) | np.roll(black, -1, 1))
    out.append({**it, 'score': round(float(wb.mean()), 4), 'size': [w, h]})
json.dump(out, open('work/gfx/sheets/label_score.json', 'w'))
pos = {11, 22, 23, 24, 43, 47, 66, 79}
for it in out[:80]:
    if it['score'] > 0.01 or it['n'] in pos: print(it['n'], it['score'], 'POS' if it['n'] in pos else '')
