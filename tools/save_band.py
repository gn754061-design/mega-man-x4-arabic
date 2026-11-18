# -*- coding: utf-8 -*-
"""Save a magnified 8x8 atlas band as PNG for visual confirmation."""
from PIL import Image

P = "./_work_ar/"arc\LOAD_U\00010001.bin'
OUT = "./_work_ar/"disc\font\atlas_band_40_5F.png'
blob = open(P, 'rb').read()
W = H = 256
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)

cols, cw, ch = 32, 8, 8
S = 6
x0 = 0
y0 = 0x40 // cols * ch          # band row for 0x40..0x5F
w = 32 * cw
h = ch
img = Image.new('L', (w * S, h * S), 30)
ip = img.load()
for y in range(h):
    for x in range(w):
        v = px[(y0 + y) * W + (x0 + x)]
        c = 30 + v * 14
        for sy in range(S):
            for sx in range(S):
                ip[x * S + sx, y * S + sy] = c
img.save(OUT)
print('saved', OUT, img.size)

# also a whole-atlas 1bpp mask at 2x for overview
ov = Image.new('L', (W * 2, H * 2), 0)
op = ov.load()
for y in range(H):
    for x in range(W):
        if px[y * W + x]:
            for sy in range(2):
                for sx in range(2):
                    op[x * 2 + sx, y * 2 + sy] = 255
o = "./_work_ar/"disc\font\atlas_overview.png'
ov.save(o)
print('saved', o, ov.size)