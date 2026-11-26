# -*- coding: utf-8 -*-
"""Render the word JUNGLE (codes 0x53 0x5E 0x57 0x50 0x55 0x4E) under candidate grids."""
P = r'./_work_ar\arc\LOAD_U\00010001.bin'
blob = open(P, 'rb').read()
W = H = 256
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)

WORD = [0x53, 0x5E, 0x57, 0x50, 0x55, 0x4E]
RAMP = ' .:-=+*#%@'


def render(cw, ch, label):
    cols = W // cw
    print('=' * 78)
    print('%s  (cell %dx%d, cols=%d, rows=%d, cells=%d)'
          % (label, cw, ch, cols, H // ch, cols * (H // ch)))
    canvas = []
    for gy in range(ch):
        row = ''
        for g in WORD:
            cx = g % cols
            cy = g // cols
            x0 = cx * cw
            y0 = cy * ch
            for x in range(cw):
                v = px[(y0 + gy) * W + x0 + x] if (y0 + gy) < H else 0
                row += RAMP[min(9, v)]
            row += ' '
        canvas.append(row)
    for r in canvas:
        print('  ' + r)


for cw, ch, lab in [(8, 16, '8x16'), (8, 8, '8x8'), (16, 16, '16x16'),
                    (16, 8, '16x8'), (12, 12, '12x12')]:
    render(cw, ch, lab)