# -*- coding: utf-8 -*-
"""Scan the PS1 EXE and small ARCs for MMX4 text codes (menus / UI strings)."""
import os
import struct

WORK = r'./_work_ar'
GLYPHS = set(range(0x40, 0x7E)) | {0x1FF} | set(range(0x83, 0x8C)) | set(range(0x200, 0x300))

targets = [
    ('EXE', os.path.join(WORK, 'disc', 'extracted', 'SLUS_005.61')),
    ('CAPCOM', os.path.join(WORK, 'arc', 'CAPCOM', '00010002.bin')),
    ('LOAD_U/0x10007', os.path.join(WORK, 'arc', 'LOAD_U', '00010007.bin')),
    ('LOAD_U/0x10008', os.path.join(WORK, 'arc', 'LOAD_U', '00010008.bin')),
    ('FONT8X8/0', os.path.join(WORK, 'arc', 'FONT8X8', '00000000.bin')),
    ('FONT8X8/1', os.path.join(WORK, 'arc', 'FONT8X8', '00000001.bin')),
    ('MOJIPAT', os.path.join(WORK, 'arc', 'MOJIPAT', '00000000.bin')),
]

for label, p in targets:
    if not os.path.isfile(p):
        print('%-18s MISSING' % label)
        continue
    data = open(p, 'rb').read()
    n = len(data) // 2
    codes = struct.unpack('<%dH' % n, data[:n * 2]) if n else ()
    blocks = []
    start = 0
    for i, c in enumerate(codes):
        if c & 0x8000:
            if i - start >= 3:
                blocks.append(codes[start:i + 1])
            start = i + 1
    good = 0
    for b in blocks:
        g = [c & 0x7FF for c in b if not (c & 0x2000)]
        if not g:
            continue
        hits = sum(1 for x in g if x in GLYPHS)
        if hits / len(g) >= 0.9:
            good += 1
    ratio = (good / len(blocks)) if blocks else 0
    print('%-18s size=%8d  blocks=%5d  glyph-valid=%4d  ratio=%.2f'
          % (label, len(data), len(blocks), good, ratio))
    for b in blocks[:3]:
        g = [c & 0x7FF for c in b if not (c & 0x2000)]
        hits = sum(1 for x in g if x in GLYPHS)
        if g and hits / len(g) >= 0.9:
            print('     ', ' '.join('%03X' % x for x in g[:18]))
            break