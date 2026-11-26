# -*- coding: utf-8 -*-
"""Scan every extracted ARC member for MMX4 text blocks (u16 glyph codes)."""
import os
import struct

ARC = r'./_work_ar\arc'

KNOWN = set(range(0x40, 0x7E)) | {0x1FF} | set(range(0x83, 0x8C))
END, BOX = 0x8000, 0x2000


def score(codes):
    """How text-like is this code array?"""
    if len(codes) < 6:
        return 0
    ends = 0
    boxes = 0
    known = 0
    total = 0
    for c in codes:
        if c & END:
            ends += 1
            continue
        if c & BOX:
            boxes += 1
        g = c & 0x7FF
        total += 1
        if g in KNOWN or g >= 0x200:
            known += 1
    if total == 0:
        return 0
    ratio = known / total
    if ratio < 0.85:
        return 0
    return ends + boxes * 2 + int(ratio * 10)


results = []
for dirpath, _, files in os.walk(ARC):
    for f in sorted(files):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(dirpath, f)
        data = open(p, 'rb').read()
        n = len(data) // 2
        if n < 16:
            continue
        codes = struct.unpack('<%dH' % n, data[:n * 2])
        # split into 0x8000-terminated blocks
        start = 0
        best = 0
        blocks = 0
        for i, c in enumerate(codes):
            if c & END:
                blk = codes[start:i + 1]
                if len(blk) >= 8:
                    blocks += 1
                    s = score(blk)
                    best = max(best, s)
                start = i + 1
        if blocks:
            results.append((best, blocks, p))

results.sort(key=lambda r: -r[0])
print('members with 0x8000-terminated blocks:', len(results))
for best, blocks, p in results[:25]:
    print('  score=%3d blocks=%4d  %s' % (best, blocks, os.path.relpath(p, ARC)))