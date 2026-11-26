# -*- coding: utf-8 -*-
"""Export candidate members as PNGs so the menu can be identified visually."""
import os
from PIL import Image

ARC = r'./_work_ar\arc'
OUT = r'./_work_ar\out\candidates'
os.makedirs(OUT, exist_ok=True)

CANDS = [
    ('PL00_U', '00010206.bin', 320, 240),
    ('PL00_U', '00000002.bin', 320, 240),
    ('PL00_U', '00020101.bin', 320, 240),
    ('PL00_U', '00020000.bin', 320, 240),
    ('PL00_U', '00000003.bin', 128, 256),
    ('PL00_U', '00010007.bin', 256, 256),
    ('PL00_U', '00010008.bin', 256, 256),
    ('PL00_U', '00020301.bin', 128, 256),
]

PAL = []
for v in range(16):
    c = v * 17
    PAL.extend([c, c, c])
PAL.extend([0, 0, 0] * (256 - 16))

for arc, f, w, h in CANDS:
    p = os.path.join(ARC, arc, f)
    if not os.path.isfile(p):
        continue
    blob = open(p, 'rb').read()
    need = (w * h) // 2
    if len(blob) < need:
        print('skip %-18s (needs %d, has %d)' % (f, need, len(blob)))
        continue
    px = bytearray(w * h)
    for i in range(w * h):
        b = blob[i // 2]
        px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)
    img = Image.frombytes('P', (w, h), bytes(px))
    img.putpalette(PAL)
    name = '%s_%s_%dx%d.png' % (arc, f.split('.')[0], w, h)
    img.save(os.path.join(OUT, name))
    print('wrote', name)

print()
print('candidates dir:', OUT)