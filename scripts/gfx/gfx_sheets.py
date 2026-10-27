"""Contact sheets of every unique 2D texture (FLASH/ID/MEDIA), 80 per sheet, labelled by sheet index."""
import sys, json, os
sys.path.insert(0, '.')
from PIL import Image, ImageDraw
from tools import cpk, pix, gim
occ = json.load(open('work/gfx/_occ.json'))
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
items = sorted(((v[0], h, len(v)) for h, v in occ.items() if any(x.startswith(('FLASH/', 'ID/', 'MEDIA/')) for x in v)))
cache = {}
def tex(ref):
    p, i = ref.split('#')
    if p not in cache:
        cache.clear(); cache[p] = pix.textures(a.read(P[p]))
    return cache[p][int(i)]
index = []
os.makedirs('work/gfx/sheets', exist_ok=True)
T, cols, rows = 120, 10, 8
for s in range(0, len(items), cols * rows):
    W = Image.new('RGB', (cols * T, rows * (T + 12)), (90, 0, 90)); d = ImageDraw.Draw(W)
    for k, (ref, h, n) in enumerate(items[s:s + cols * rows]):
        w_, h_, rgba = gim.decode(tex(ref))
        im = Image.frombytes('RGBA', (w_, h_), rgba); im.thumbnail((T - 2, T - 2))
        x, y = (k % cols) * T, (k // cols) * (T + 12)
        W.paste(im, (x + 1, y + 12), im); d.text((x + 1, y), f'{s + k} x{n}', fill='yellow')
        index.append({'n': s + k, 'hash': h, 'first': ref, 'count': n})
    W.save(f'work/gfx/sheets/s{s // (cols * rows):03d}.png')
json.dump(index, open('work/gfx/sheets/index.json', 'w'))
print(len(items), 'textures', -(-len(items) // (cols * rows)), 'sheets')
