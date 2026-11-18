# -*- coding: utf-8 -*-
"""Render one atlas band (cells 0x40..0x5F) at 8x8 and 8x16 to confirm the glyph order."""
P = "./_work_ar/"arc\LOAD_U\00010001.bin'
blob = open(P, 'rb').read()
W = H = 256
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)
RAMP = ' .:-=+*#%@'

for cw, ch, cols in [(8, 8, 32), (8, 16, 32)]:
    print('=' * 90)
    print('cell %dx%d cols=%d  -- band 0x40..0x5F' % (cw, ch, cols))
    rows = ch
    for gy in range(rows):
        line = ''
        for g in range(0x40, 0x60):
            cx = g % cols
            cy = g // cols
            x0, y0 = cx * cw, cy * ch
            for x in range(cw):
                v = px[(y0 + gy) * W + x0 + x] if (y0 + gy) < H else 0
                line += RAMP[min(9, v)]
            line += '|'
        print('  ' + line)
    print('  ' + ''.join('%-8s|' % ('%02X' % (0x40 + i)) for i in range(0, 32)))
    print()