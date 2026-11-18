# -*- coding: utf-8 -*-
"""Identify which LOAD_U member holds menu/UI artwork."""
import os
from PIL import Image

EX = "./_work_ar/"arc\LOAD_U'
OUT = "./_work_ar/"disc\font'
os.makedirs(OUT, exist_ok=True)
W = H = 256
RAMP = ' .:-=+*#%@'


def to_px(blob):
    px = bytearray(W * H)
    for i in range(W * H):
        b = blob[i // 2]
        px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)
    return px


def stats(px):
    nz = sum(1 for v in px if v)
    return nz, 100.0 * nz / len(px)


for f in sorted(os.listdir(EX)):
    if not f.endswith('.bin'):
        continue
    blob = open(os.path.join(EX, f), 'rb').read()
    px = to_px(blob)
    nz, pct = stats(px)
    print('%-16s %6d bytes  nonzero=%5d (%.1f%%)' % (f, len(blob), nz, pct))

    # render
    img = Image.frombytes('P', (W, H), bytes(px))
    pal = []
    for v in range(16):
        c = v * 17
        pal.extend([c, c, c])
    pal.extend([0, 0, 0] * (256 - 16))
    img.putpalette(pal)
    img.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(OUT, 'lu_%s.png' % f.split('.')[0]))

    # ascii dump of first 4 bands (rows 0..63)
    print('   rows 0..63:')
    for y in range(0, 64):
        line = ''.join(RAMP[min(9, px[y * W + x])] for x in range(128))
        if line.strip():
            print('   %3d %s' % (y, line))
    print()