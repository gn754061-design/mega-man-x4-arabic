# -*- coding: utf-8 -*-
"""Check whether atlas cells 0x100-0x1FF are UI glyphs or artwork."""
import os

P = r'C:\Users\user\Desktop\m x4\_work_ar\arc\LOAD_U\00010001.bin'
at = open(P, 'rb').read()
W = 256
RAMP = ' .:-=+*#%@'


def px(x, y):
    i = y * W + x
    b = at[i // 2]
    return (b >> 4) if i % 2 == 0 else (b & 0x0F)


for base in (0x100, 0x140, 0x180):
    print('=' * 60)
    print('cells 0x%03X..0x%03X (first 8 cells of the row band)' % (base, base + 7))
    for k in range(8):
        cell = base + k
        cx = (cell % 32) * 8
        cy = (cell // 32) * 8
        rows = []
        for y in range(8):
            rows.append(''.join(RAMP[min(9, px(cx + x, cy + y))] for x in range(8)))
        print('  0x%03X: %s' % (cell, ' | '.join(rows)))

# occupancy per 0x20 block in 0x000..0x1FF
print()
print('occupancy by 0x20 block:')
for b in range(0, 512, 32):
    nz = 0
    for cell in range(b, b + 32):
        cx = (cell % 32) * 8
        cy = (cell // 32) * 8
        s = 0
        for y in range(8):
            for x in range(8):
                s |= px(cx + x, cy + y)
        if s:
            nz += 1
    print('  0x%03X-0x%03X : %2d/32 used' % (b, b + 31, nz))