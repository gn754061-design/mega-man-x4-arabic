# -*- coding: utf-8 -*-
"""Occupancy analysis of the dialogue atlas to infer real dimensions and free space."""
import os
from PIL import Image

EX = "./_work_ar/"arc\LOAD_U\00010001.bin'
OUT = "./_work_ar/"disc\font'

blob = open(EX, 'rb').read()

# 4bpp linear: 2 pixels per byte
w = h = 256
px = bytearray(w * h)
for i in range(w * h):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)

nonzero = sum(1 for v in px if v)
print('4bpp 256x256: nonzero px %d / %d (%.1f%%)' % (nonzero, len(px), 100.0 * nonzero / len(px)))

cols = [0] * w
rows = [0] * h
for y in range(h):
    base = y * w
    for x in range(w):
        if px[base + x]:
            cols[x] += 1
            rows[y] += 1

first_col = next((x for x in range(w) if cols[x]), None)
last_col = next((x for x in range(w - 1, -1, -1) if cols[x]), None)
first_row = next((y for y in range(h) if rows[y]), None)
last_row = next((y for y in range(h - 1, -1, -1) if rows[y]), None)
print('used columns: %s..%s   used rows: %s..%s' % (first_col, last_col, first_row, last_row))

# find empty horizontal bands (candidate cell grid)
print()
print('row bands (first 40):')
run = None
bands = []
for y in range(h):
    if rows[y] == 0:
        if run is None:
            run = y
    else:
        if run is not None:
            bands.append((run, y - 1))
            run = None
if run is not None:
    bands.append((run, h - 1))
print('empty row bands:', bands[:20])
print('total empty row bands:', len(bands))

# render the used region as ASCII art at 1 char per pixel, thresholded
print()
print('ASCII map (rows 0..%d, cols 0..%d), 1 char = 1 px' % (min(h, 96), min(w, 128)))
for y in range(0, min(h, 96)):
    line = ''.join('#' if px[y * w + x] else '.' for x in range(min(w, 128)))
    if '#' in line:
        print('%3d %s' % (y, line))