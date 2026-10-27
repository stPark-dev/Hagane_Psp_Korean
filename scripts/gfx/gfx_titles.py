"""Find the chapter-title atlases (white text on a transparent 256x256 texture) and match their titles to EBOOT.

Writes work/gfx/titles.png (each candidate, labelled with its hash). Titles are read by eye; pass them as
arguments to check them against the src_sha1 of text/ko/eboot.json (cp932 SHA-1), e.g.
    python3 scripts/gfx/gfx_titles.py 二人の錬金術師 賢者の石
"""
import sys, json, hashlib
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
from tools import cpk, pix, gim
occ = json.load(open('work/gfx/_occ.json'))
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
byfile = {}
for h, v in occ.items():
    p, i = v[0].split('#')
    if p.startswith('FLASH/'):
        byfile.setdefault(p, []).append((int(i), h, v))
hits = []
for p, lst in sorted(byfile.items()):
    ts = pix.textures(a.read(P[p]))
    for i, h, v in lst:
        w, hh, rgba = gim.decode(ts[i])
        if (w, hh) != (256, 256):
            continue
        A = np.frombuffer(rgba, np.uint8).reshape(hh, w, 4).astype(int)
        op = A[..., 3] > 128; lum = A[..., :3].mean(-1)
        sat = (A[..., :3].max(-1) - A[..., :3].min(-1))[op]
        # mostly transparent, opaque pixels all white or near-grey: titles; cut-in art and labels fail this
        if (A[..., 3] == 0).mean() > 0.5 and ((lum > 200) & op).mean() > 0.04 and (op & (lum <= 200)).mean() < 0.02 \
                and sat.size and sat.mean() < 10:
            hits.append((v[0], h, len(v), Image.frombytes('RGBA', (w, hh), rgba)))
hits.sort()
W = Image.new('RGBA', (4 * 260, -(-len(hits) // 4) * 272), (60, 0, 60, 255)); d = ImageDraw.Draw(W)
for k, (ref, h, n, im) in enumerate(hits):
    x, y = (k % 4) * 260, (k // 4) * 272
    W.alpha_composite(im, (x, y + 16)); d.text((x + 2, y + 2), f'{h} x{n} {ref}', fill='yellow')
W.save('work/gfx/titles.png')
for ref, h, n, _ in hits:
    print(h, n, ref)
ko = {e['src_sha1']: e for e in json.load(open('text/ko/eboot.json', encoding='utf-8'))['entries']}
for t in sys.argv[1:]:
    e = ko.get(hashlib.sha1(t.encode('cp932')).hexdigest()[:12])
    print(t, '->', f"{e['id']} {e['ko']}" if e else 'no EBOOT string')
