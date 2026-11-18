# -*- coding: utf-8 -*-
"""Locate menu tiles: score members for fixed-width 8x8 text-tile structure."""
import os
import struct

ARC = "./_work_ar/"arc'
RAMP = ' .:-=+*#%@'


def to_px4(blob, w, h):
    need = (w * h) // 2
    if len(blob) < need:
        return None
    px = bytearray(w * h)
    for i in range(w * h):
        b = blob[i // 2]
        px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)
    return px


def tile_score(px, w, h):
    """Fraction of 8x8 tiles that look like glyphs (moderate ink, left-right centred)."""
    cols, rows = w // 8, h // 8
    good = 0
    total = 0
    for ty in range(rows):
        for tx in range(cols):
            ink = 0
            minx, maxx = 99, -1
            for y in range(8):
                for x in range(8):
                    if px[(ty * 8 + y) * w + (tx * 8 + x)]:
                        ink += 1
                        minx = min(minx, x)
                        maxx = max(maxx, x)
            total += 1
            if 4 <= ink <= 34 and minx <= 3 and maxx >= 4:
                good += 1
    return good / max(1, total), good, total


cands = []
for arc in ('PL00_U', 'PL01_U', 'PL02_U'):
    d = os.path.join(ARC, arc)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(d, f)
        blob = open(p, 'rb').read()
        best = (0, None)
        for w, h in [(256, 256), (320, 240), (512, 256), (256, 512), (128, 256)]:
            px = to_px4(blob, w, h)
            if px is None:
                continue
            r, g, t = tile_score(px, w, h)
            if r > best[0]:
                best = (r, (w, h, g, t))
        if best[1]:
            cands.append((best[0], p, best[1]))

cands.sort(key=lambda c: -c[0])
print('%-6s %-6s %-9s %-22s %s' % ('score', 'good', 'total', 'file', 'geometry'))
for r, p, (w, h, g, t) in cands[:18]:
    print('%.3f  %5d  %6d  %-22s %dx%d' % (r, g, t, os.path.relpath(p, ARC), w, h))