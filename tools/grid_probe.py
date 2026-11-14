# -*- coding: utf-8 -*-
"""Brute-force the atlas cell geometry by rendering glyph 0x53 ('J') under several grids."""
import os

P = r'C:\Users\user\Desktop\m x4\_work_ar\arc\LOAD_U\00010001.bin'
blob = open(P, 'rb').read()

W = H = 256
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)


def cell(cx, cy, cw, ch, cols, cw_, ch_):
    """Extract cell (cx,cy) of size cw_ x ch_ from a grid of cw x ch cells."""
    x0 = (cx % cols) * cw_
    y0 = (cx // cols) * ch_
    rows = []
    for y in range(ch_):
        r = ''
        for x in range(cw_):
            v = px[(y0 + y) * W + (x0 + x)] if (y0 + y) < H and (x0 + x) < W else 0
            r += ' .:-=+*#%@'[min(9, v)]
        rows.append(r)
    return rows


candidates = [
    ('16x16 cell, 16 cols', 16, 16),
    ('8x16 cell, 32 cols', 8, 16),
    ('8x8 cell, 32 cols', 8, 8),
    ('16x8 cell, 16 cols', 16, 8),
    ('12x16 cell, 21 cols', 12, 16),
    ('16x16 cell, 16 cols (x2)', 16, 16),
]

TARGET = 0x53  # 'J'

for name, cw, ch in candidates:
    if name.endswith('(x2)'):
        continue
    cols = W // cw
    print('=' * 70)
    print('%s  (cols=%d, rows=%d, total cells=%d)' % (name, cols, H // ch, cols * (H // ch)))
    cx = TARGET % cols
    cy = TARGET // cols
    if cy >= H // ch:
        print('  glyph out of range')
        continue
    for r in cell(cx, cy, cw, ch, cols, cw, ch):
        print('  |' + r + '|')
    print()