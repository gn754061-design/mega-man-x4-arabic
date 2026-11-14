# -*- coding: utf-8 -*-
"""Render PL00_U/00000003.bin (128x256) as ASCII."""
P = r'C:\Users\user\Desktop\m x4\_work_ar\arc\PL00_U\00000003.bin'
blob = open(P, 'rb').read()
W, H = 128, 256
RAMP = ' .:-=+*#%@'
print('bytes:', len(blob), 'need4bpp:', (W * H) // 2)
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)
nz = sum(1 for v in px if v)
print('nonzero: %d (%.1f%%)' % (nz, 100.0 * nz / len(px)))
print()
for cy in range(0, H, 2):
    line = ''
    for cx in range(0, W, 1):
        s = 0
        for y in range(2):
            v = px[(cy + y) * W + cx]
            s += v
        line += RAMP[min(9, s // 3)]
    print('%3d %s' % (cy, line))