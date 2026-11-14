# -*- coding: utf-8 -*-
"""Find text blocks that use the UI glyph range (0x8C-0x1FE).

The dialogue table uses only 0x40-0x8B + 0x1FF. The atlas still has ~369 used
cells in 0x8C-0x1FE, which must belong to a second (menu/UI) font set.
"""
import os
import struct

WORK = r'C:\Users\user\Desktop\m x4\_work_ar'
UI_LO, UI_HI = 0x8C, 0x1FE
GLYPHS = set(range(0x8C, 0x1FF)) | set(range(0x40, 0x8C)) | set(range(0x200, 0x280))


def scan(codes):
    blocks = []
    start = 0
    for i, c in enumerate(codes):
        if c & 0x8000:
            if i - start >= 3:
                blocks.append(codes[start:i + 1])
            start = i + 1
    good = []
    for b in blocks:
        g = [c & 0x7FF for c in b if not (c & 0x2000)]
        if not g:
            continue
        ui = sum(1 for x in g if UI_LO <= x <= UI_HI)
        if ui / len(g) >= 0.9:
            good.append(g)
    return blocks, good


files = []
for r in [os.path.join(WORK, 'arc'), os.path.join(WORK, 'disc', 'extracted')]:
    for dp, _, fs in os.walk(r):
        for f in fs:
            if f.endswith('.bin') or f == 'SLUS_005.61':
                files.append(os.path.join(dp, f))

print('files:', len(files))
found = []
for p in files:
    data = open(p, 'rb').read()
    n = len(data) // 2
    if n < 8:
        continue
    codes = struct.unpack('<%dH' % n, data[:n * 2])
    blocks, good = scan(codes)
    if len(good) >= 5:
        found.append((len(good), p, good))

found.sort(key=lambda r: -r[0])
print('files with >=5 UI-range text blocks:', len(found))
for cnt, p, good in found[:12]:
    print('\n  %s : %d blocks' % (os.path.relpath(p, WORK), cnt))
    for g in good[:6]:
        print('     ', ' '.join('%03X' % x for x in g[:24]))