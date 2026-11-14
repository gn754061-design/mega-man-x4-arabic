# -*- coding: utf-8 -*-
"""Verify the atlas inside the patched disc and render the Arabic block."""
import os
import struct
from PIL import Image

WORK = r'C:\Users\user\Desktop\m x4\_work_ar'
OUT = os.path.join(WORK, 'out')
USER = 2048

ents = {}
for line in open(os.path.join(WORK, 'disc', 'files.txt'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        ents[p[0]] = (int(p[1]), int(p[2]))

data = open(os.path.join(OUT, 'Megaman X4 (Arabic).bin'), 'rb').read()


def arc_blob(name):
    lba, size = ents[name]
    out = bytearray()
    got, sec = 0, lba
    while got < size:
        out += data[sec * 2352 + 24: sec * 2352 + 24 + USER]
        got += USER
        sec += 1
    return bytes(out[:size])


blob = arc_blob('ARC/LOAD_U.ARC')
count = struct.unpack('<I', blob[:4])[0]
off = 0x800
atlas = None
for i in range(count):
    if i == 0:
        t, s = struct.unpack('<II', blob[8:16])
    else:
        t, s = struct.unpack('<II', blob[0x10 + (i - 1) * 8:0x18 + (i - 1) * 8])
    if t == 0x00010001:
        atlas = blob[off:off + s]
    off += s
    if s % 0x800:
        off += 0x800 - (s % 0x800)

print('atlas member bytes:', len(atlas) if atlas else None)
orig = open(os.path.join(WORK, 'arc', 'LOAD_U', '00010001.bin'), 'rb').read()
print('matches generated :', atlas == orig)

W = H = 256


def px(buf, x, y):
    i = y * W + x
    b = buf[i // 2]
    return (b >> 4) if i % 2 == 0 else (b & 0x0F)


# count non-empty cells in 0x200..0x27F
filled = 0
for cell in range(0x200, 0x280):
    cx = (cell % 32) * 8
    cy = (cell // 32) * 8
    s = 0
    for y in range(8):
        for x in range(8):
            s |= px(atlas, cx + x, cy + y)
    if s:
        filled += 1
print('arabic cells filled: %d / 128' % filled)

# render 0x200..0x23F (64 cells = 2 rows) at 8x
S = 8
w = 32 * 8
h = 2 * 8
img = Image.new('L', (w * S, h * S), 0)
ip = img.load()
for y in range(h):
    for x in range(w):
        if px(atlas, x, 0x200 // 32 * 8 + y):
            for sy in range(S):
                for sx in range(S):
                    ip[x * S + sx, y * S + sy] = 255
p = os.path.join(OUT, 'arabic_glyphs_preview.png')
img.save(p)
print('preview:', p, img.size)