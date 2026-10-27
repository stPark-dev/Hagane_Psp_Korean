"""mash.py OUTDIR PREFIX SECONDS [button] : press button every 0.8s, screenshot every 10s"""
import sys, time
sys.path.insert(0, '.')
from tools import ppdbg
out, pre, secs = sys.argv[1], sys.argv[2], float(sys.argv[3])
btns = (sys.argv[4] if len(sys.argv) > 4 else 'circle').split(',')
d = ppdbg.Debugger()
t0 = time.time(); n = 0; last = -10; n_press = 0
while time.time() - t0 < secs:
    d.press(btns[n_press % len(btns)], 0.08); n_press += 1; time.sleep(0.7)
    if time.time() - last >= 10:
        ppdbg.capture_window(f'{out}/{pre}{n:02d}.png'); n += 1; last = time.time()
print('shots', n)
