# -*- coding: utf-8 -*-
"""Dump FONT8X8.ARC as candidate 8x8 1bpp glyphs into a PNG contact sheet."""
import os
from PIL import Image

SRC = r'C:\Users\user\Desktop\m x4\_work_ar\disc\extracted\ARC_FONT8X8.ARC'
OUT = r'C:\Users\user\Desktop\m x4\_work_ar\disc\font8x8_sheet.png'

blob = open(SRC, 'rb').read()
print('file bytes:', len(blob))
print('first 64:', blob[:64].hex(' '))

# try several header sizes; each glyph = 8 bytes (8x8 1bpp)
for hdr in (0, 16, 32, 64):
    body = blob[hdr:]
    n = len(body) // 8
    print('header %3d -> %d glyphs of 8 bytes' % (hdr, n))

HDR = 32
body = blob[HDR:]
n = len(body) // 8
COLS = 32
ROWS = (n + COLS - 1) // COLS
SCALE = 4
sheet = Image.new('L', (COLS * 8 * SCALE + COLS, ROWS * 8 * SCALE + ROWS), 40)
px = sheet.load()

nonzero = 0
for g in range(n):
    cx = (g % COLS) * (8 * SCALE + 1)
    cy = (g // COLS) * (8 * SCALE + 1)
    data = body[g * 8:g * 8 + 8]
    if any(data):
        nonzero += 1
    for y in range(8):
        row = data[y]
        for x in range(8):
            if row & (0x80 >> x):
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        px[cx + x * SCALE + sx, cy + y * SCALE + sy] = 230

print('glyphs:', n, 'non-empty:', nonzero)
sheet.save(OUT)
print('sheet:', OUT, sheet.size)