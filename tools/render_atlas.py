# -*- coding: utf-8 -*-
"""Render LOAD_U member 0x10001 (dialogue atlas) under several candidate layouts."""
import os
from PIL import Image

EX = r'./_work_ar\arc'
OUT = r'./_work_ar\disc\font'
os.makedirs(OUT, exist_ok=True)

blob = open(os.path.join(EX, 'LOAD_U', '00010001.bin'), 'rb').read()
print('bytes:', len(blob))
print('first 64:', blob[:64].hex(' '))

# candidate palettes: 16-grey and a 16-colour ramp
ramp = [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 128, 128), (255, 128, 0),
        (128, 0, 255), (0, 128, 255), (128, 255, 0), (255, 0, 128), (0, 255, 128),
        (128, 255, 255)]

for i, c in enumerate(ramp):
    pass


def render4(data, w, h, path, pal):
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            byte = data[(y * w + x) // 2]
            v = (byte >> 4) if (x % 2 == 0) else (byte & 0x0F)
            row.append(v)
        rows.append(bytes(row))
    need = (w * h) // 2
    if len(data) < need:
        return None
    img = Image.frombytes('P', (w, h), b''.join(rows))
    flat = []
    for c in pal:
        flat.extend(c)
    flat.extend([0, 0, 0] * (256 - len(pal)))
    img.putpalette(flat)
    img.save(path)
    return img.size


cands = [
    ('4bpp_256x256', 256, 256),
    ('4bpp_512x128', 512, 128),
    ('4bpp_128x512', 128, 512),
    ('4bpp_256x512_hi', 256, 512),
]
for name, w, h in cands:
    p = os.path.join(OUT, 'load_0x10001_%s.png' % name)
    r = render4(blob, w, h, p, ramp)
    print('%-18s %s -> %s' % (name, r, p))

# FONT8X8 member 0
f8 = open(os.path.join(EX, 'FONT8X8', '00000000.bin'), 'rb').read()
print()
print('FONT8X8/0 bytes:', len(f8), 'first 32:', f8[:32].hex(' '))
p = os.path.join(OUT, 'font8x8_0_1bpp.png')
COLS, ROWS, S = 32, 16, 4
n = len(f8) // 8
sheet = Image.new('L', (COLS * 8 * S + COLS, ROWS * 8 * S + ROWS), 40)
px = sheet.load()
for g in range(min(n, COLS * ROWS)):
    cx = (g % COLS) * (8 * S + 1)
    cy = (g // COLS) * (8 * S + 1)
    d = f8[g * 8:g * 8 + 8]
    for y in range(8):
        for x in range(8):
            if d[y] & (0x80 >> x):
                for sy in range(S):
                    for sx in range(S):
                        px[cx + x * S + sx, cy + y * S + sy] = 235
sheet.save(p)
print('font8x8 sheet:', p, sheet.size)