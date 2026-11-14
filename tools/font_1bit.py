# -*- coding: utf-8 -*-
"""Rebuild the Arabic glyphs with 1-bit (non-antialiased) masks to preserve dots."""
import json
import os

import arabic_reshaper
from PIL import ImageFont

WORK = r'C:\Users\user\Desktop\m x4\_work_ar'
FONT_CANDIDATES = [
    (r'C:\Windows\Fonts\arabtype.ttf', 8),
    (r'C:\Windows\Fonts\simpo.ttf', 8),
    (r'C:\Windows\Fonts\trado.ttf', 8),
    (r'C:\Windows\Fonts\candarab.ttf', 8),
    (r'C:\Windows\Fonts\arial.ttf', 8),
    (r'C:\Windows\Fonts\segoeui.ttf', 8),
]
CELL = 8

reshaper = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': True, 'support_ligatures': True})

cat = json.load(open(os.path.join(WORK, 'out', 'ar_catalog.json'), encoding='utf-8'))
needed = set()
for e in cat['entries']:
    t = e.get('translation', '')
    if not t.strip():
        continue
    for line in t.replace('\f', '\n').split('\n'):
        if line.strip():
            for ch in reshaper.reshape(line):
                if ch != ' ':
                    needed.add(ch)
needed = sorted(needed)


def render_set(font_path, size):
    font = ImageFont.truetype(font_path, size)
    out = {}
    for ch in needed:
        try:
            m = font.getmask(ch, mode='1')
        except Exception:
            continue
        if m.size == (0, 0):
            continue
        w, h = m.size
        if w <= 0 or h <= 0:
            continue
        bm = [[0] * CELL for _ in range(CELL)]
        ox = (CELL - w) // 2
        oy = CELL - h
        if ox < 0 or oy < 0:
            continue
        for y in range(h):
            for x in range(w):
                if m.getpixel((x, y)):
                    bm[oy + y][ox + x] = 1
        out[ch] = bm
    return out


best = None
for path, size in FONT_CANDIDATES:
    if not os.path.isfile(path):
        continue
    bm = render_set(path, size)
    if not bm:
        print('%-40s : no glyphs' % os.path.basename(path))
        continue
    sigs = {}
    for ch, g in bm.items():
        sigs.setdefault(tuple(tuple(r) for r in g), []).append(ch)
    dups = sum(1 for v in sigs.values() if len(v) > 1)
    faint = sum(1 for g in bm.values() if sum(sum(r) for r in g) <= 2)
    print('%-40s : glyphs=%3d distinct=%3d dups=%2d faint=%2d'
          % (os.path.basename(path), len(bm), len(sigs), dups, faint))
    score = (len(sigs), -dups, -faint)
    if best is None or score > best[0]:
        best = (score, path, size, bm)

print()
print('BEST:', os.path.basename(best[1]), 'size', best[2],
      'distinct', best[0][0], 'dups', -best[0][1], 'faint', -best[0][2])

json.dump({('%04X' % ord(k)): v for k, v in best[3].items()},
          open(os.path.join(WORK, 'data', 'arabic_bitmaps.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote data/arabic_bitmaps.json')