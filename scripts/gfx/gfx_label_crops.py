"""Crop the lower-right label area of label candidates into readable sheets."""
import sys, json
sys.path.insert(0, '.')
from PIL import Image, ImageDraw
from tools import cpk, pix, gim
s = [x for x in json.load(open('work/gfx/sheets/label_score.json')) if x['score'] > 0.004]
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
cache = {}
def tex(ref):
    p, i = ref.split('#')
    if p not in cache:
        cache.clear(); cache[p] = pix.textures(a.read(P[p]))
    return cache[p][int(i)]
cols, rows, CW, CH = 4, 10, 300, 88
for k0 in range(0, len(s), cols * rows):
    W = Image.new('RGB', (cols * CW, rows * CH), (40, 40, 40)); d = ImageDraw.Draw(W)
    for k, it in enumerate(s[k0:k0 + cols * rows]):
        w, h, rgba = gim.decode(tex(it['first']))
        im = Image.frombytes('RGBA', (w, h), rgba).crop((int(w * 0.42), int(h * 0.78), w, h))
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        x, y = (k % cols) * CW, (k // cols) * CH
        W.paste(im, (x + 2, y + 12), im); d.text((x + 2, y), f"{it['n']} x{it['count']} {it['score']}", fill='yellow')
    W.save(f'work/gfx/sheets/lab{k0 // (cols * rows):02d}.png')
print(len(s))
