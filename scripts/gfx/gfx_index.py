"""Index every texture in DAT000.cpk by content: work/gfx/_occ.json maps sha1(GIM)[:12] -> ["path#i", ...].

Run first; gfx_sheets.py and the other gfx scripts read this index.
"""
import sys, json, os, hashlib
sys.path.insert(0, '.')
from tools import cpk, pix
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk')
occ = {}
for e in a.entries:
    if not e.path.lower().endswith('.pix'):
        continue
    for i, g in enumerate(pix.textures(a.read(e))):
        occ.setdefault(hashlib.sha1(g).hexdigest()[:12], []).append(f'{e.path}#{i}')
os.makedirs('work/gfx', exist_ok=True)
json.dump(occ, open('work/gfx/_occ.json', 'w'))
print(sum(map(len, occ.values())), 'textures', len(occ), 'unique')
