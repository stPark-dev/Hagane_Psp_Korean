"""drive.py OUTDIR step... ; step = button[:wait] | shot:name | wait:sec | until:ref.png[:timeout] (match screen region)"""
import sys, time
sys.path.insert(0, '.')
from PIL import Image, ImageChops, ImageStat
from tools import ppdbg
out = sys.argv[1]
d = ppdbg.Debugger()
def diff(a, b):
    a = a.convert('L').resize((240, 136)); b = b.convert('L').resize((240, 136))
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)
for step in sys.argv[2:]:
    k, _, v = step.partition(':')
    if k == 'shot': ppdbg.capture_window(f'{out}/{v}.png')
    elif k == 'wait': time.sleep(float(v))
    elif k == 'until':
        ref, _, to = v.partition(':'); r = Image.open(ref); t0 = time.time()
        while True:
            ppdbg.capture_window(f'{out}/_cur.png'); dv = diff(Image.open(f'{out}/_cur.png'), r)
            if dv < 12: print('matched', ref, round(time.time() - t0)); break
            if time.time() - t0 > float(to or 240): print('TIMEOUT', ref, dv); sys.exit(1)
            time.sleep(1)
    else:
        d.press(k); time.sleep(float(v or 0.6))
