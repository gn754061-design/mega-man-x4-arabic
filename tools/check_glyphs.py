# -*- coding: utf-8 -*-
"""Mechanical legibility checks on the generated Arabic glyphs."""
import json
import os
import collections

WORK = r'./_work_ar'
enc = json.load(open(os.path.join(WORK, 'data', 'arabic_encode.json'), encoding='utf-8'))
at = open(os.path.join(WORK, 'arc', 'LOAD_U', '00010001.bin'), 'rb').read()
W = 256
COLS = 32
CELL = 8


def bits(code):
    cx = (code % COLS) * CELL
    cy = (code // COLS) * CELL
    rows = []
    for y in range(CELL):
        v = 0
        for x in range(CELL):
            i = (cy + y) * W + (cx + x)
            b = at[i // 2]
            px = (b >> 4) if i % 2 == 0 else (b & 0x0F)
            if px:
                v |= 0x80 >> x
        rows.append(v)
    return tuple(rows)


placed = {int(v): int(k, 16) for k, v in enc['placed'].items()}
sigs = collections.defaultdict(list)
lowink = []
for cell, cp in sorted(placed.items()):
    bm = bits(cell)
    ink = sum(bin(v).count('1') for v in bm)
    sigs[bm].append((cell, cp))
    if ink <= 2:
        lowink.append((cell, cp, ink))

dups = {k: v for k, v in sigs.items() if len(v) > 1}
print('glyphs placed        : %d' % len(placed))
print('distinct bitmaps     : %d' % len(sigs))
print('duplicate groups     : %d' % len(dups))
print('glyphs with ink<=2   : %d' % len(lowink))
print()
for bm, items in list(dups.items())[:12]:
    print('  dup: ' + ', '.join('U+%04X@%03X' % (cp, c) for c, cp in items))
print()
for c, cp, ink in lowink[:12]:
    print('  faint: U+%04X@%03X ink=%d' % (cp, c, ink))

# rendered-page ink profile: every used cell must have ink in the composed page
tot_ink = 0
for cell in placed:
    tot_ink += sum(bin(v).count('1') for v in bits(cell))
print()
print('total glyph ink pixels: %d' % tot_ink)
print('avg ink per glyph     : %.1f' % (tot_ink / max(1, len(placed))))