# -*- coding: utf-8 -*-
"""Strict text-surface detector: fraction of codes that are valid MMX4 glyphs."""
import os
import struct

ARC = "./_work_ar/"arc'
GLYPHS = set(range(0x40, 0x7E)) | {0x1FF} | set(range(0x83, 0x8C)) | set(range(0x200, 0x300))


def analyse(codes):
    blocks = []
    start = 0
    for i, c in enumerate(codes):
        if c & 0x8000:
            if i - start >= 4:
                blocks.append(codes[start:i + 1])
            start = i + 1
    good = 0
    total = 0
    for b in blocks:
        g = [c & 0x7FF for c in b if not (c & 0x2000)]
        if not g:
            continue
        total += 1
        hits = sum(1 for x in g if x in GLYPHS)
        if hits / len(g) >= 0.95:
            good += 1
    return len(blocks), good, (good / total if total else 0.0)


results = []
for dirpath, _, files in os.walk(ARC):
    for f in sorted(files):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(dirpath, f)
        data = open(p, 'rb').read()
        n = len(data) // 2
        if n < 32:
            continue
        codes = struct.unpack('<%dH' % n, data[:n * 2])
        blocks, good, ratio = analyse(codes)
        if good >= 20:
            results.append((good, ratio, blocks, p))

results.sort(key=lambda r: -r[0])
print('members with >=20 glyph-valid text blocks:', len(results))
for good, ratio, blocks, p in results[:20]:
    print('  good=%4d ratio=%.2f blocks=%4d  %s'
          % (good, ratio, blocks, os.path.relpath(p, ARC)))