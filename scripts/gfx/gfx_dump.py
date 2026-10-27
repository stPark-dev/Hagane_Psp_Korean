"""Dump textures of the given .pix files to work/gfx/*.png and write a contact sheet per file."""
import sys, os
sys.path.insert(0, '.')
from PIL import Image, ImageDraw
from tools import cpk, pix, gim
a = cpk.CpkArchive('work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk'); P = a.by_path()
os.makedirs('work/gfx', exist_ok=True)
for n in sys.argv[1:]:
    ims = []
    for i, g in enumerate(pix.textures(a.read(P[n]))):
        w, h, rgba = gim.decode(g)
        im = Image.frombytes('RGBA', (w, h), rgba)
        im.save(f"work/gfx/{n.replace('/', '_')[:-4]}_{i:02d}.png"); ims.append(im)
    cols = 4; cell = 260
    W = Image.new('RGBA', (cols * cell, -(-len(ims) // cols) * (cell + 14)), (70, 70, 70, 255)); d = ImageDraw.Draw(W)
    for k, im in enumerate(ims):
        t = im.copy(); t.thumbnail((cell - 4, cell - 4)); x, y = (k % cols) * cell, (k // cols) * (cell + 14)
        W.paste(t, (x + 2, y + 14), t); d.text((x + 3, y + 1), f'{k:02d} {im.size}', fill='yellow')
    W.save(f"work/gfx/_sheet_{n.replace('/', '_')[:-4]}.png"); print(n, len(ims))
