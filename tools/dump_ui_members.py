# -*- coding: utf-8 -*-
import os, struct
from PIL import Image

PAL = []
for v in range(16):
    c = v * 17
    PAL.extend([c, c, c])
PAL.extend([0, 0, 0] * (256 - 16))

out_dir = "./_work_ar/"out\menu_investigation'
os.makedirs(out_dir, exist_ok=True)

arc_base = "./_work_ar/"arc'
targets = ['ST0E_U0', 'ST0E_U1', 'ST0F_U1', 'ST0F_UX', 'ST0F_UZ', 'LOAD_U', 'FONT8X8']

for t in targets:
    tdir = os.path.join(arc_base, t)
    if not os.path.isdir(tdir):
        continue
    for f in os.listdir(tdir):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(tdir, f)
        blob = open(p, 'rb').read()
        size = len(blob)
        base_name = f.split('.')[0]
        # Try widths: 128, 256
        for w in [128, 256]:
            h = (size * 2) // w
            if h < 8 or h > 2048:
                continue
            px = bytearray(w * h)
            limit = min(w * h, size * 2)
            for i in range(limit):
                b = blob[i // 2]
                px[i] = (b & 0x0F) if i % 2 == 0 else (b >> 4)
            img = Image.frombytes('P', (w, h), bytes(px))
            img.putpalette(PAL)
            fn = '%s_%s_w%d_h%d.png' % (t, base_name, w, h)
            img.save(os.path.join(out_dir, fn))
            print('Wrote %s (size %d)' % (fn, size))

print('Done dumping UI members.')
