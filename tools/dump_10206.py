# -*- coding: utf-8 -*-
"""Render PL00_U/00010206.bin at 320x240 and dump an ASCII thumbnail."""
import os

P = "./_work_ar/"arc\PL00_U\00010206.bin'
blob = open(P, 'rb').read()
W, H = 320, 240
RAMP = ' .:-=+*#%@'
print('bytes:', len(blob), ' frame4bpp:', (W * H) // 2, ' frames:', len(blob) / ((W * H) // 2))

px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)

nz = sum(1 for v in px if v)
print('nonzero: %d (%.1f%%)' % (nz, 100.0 * nz / len(px)))
print()
# ASCII thumbnail: 160x60 chars (2x4 px per char)
for cy in range(0, H, 4):
    line = ''
    for cx in range(0, W, 2):
        s = 0
        for y in range(4):
            for x in range(2):
                v = px[(cy + y) * W + (cx + x)] if (cy + y) < H else 0
                s += v
        line += RAMP[min(9, s // 3)]
    print(line)