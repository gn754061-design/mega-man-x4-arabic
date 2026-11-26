# -*- coding: utf-8 -*-
"""Repair the faint/duplicate Arabic glyphs by trying several fonts per glyph."""
import json
import os

import arabic_reshaper
from PIL import ImageFont

WORK = r'./_work_ar'
CELL = 8

FONTS = [
    (r'C:\Windows\Fonts\trado.ttf', 8),
    (r'C:\Windows\fonts\simpo.ttf', 8),
    (r'C:\Windows\Fonts\arabtype.ttf', 8),
    (r'C:\Windows\Fonts\segoeui.ttf', 8),
    (r'C:\Windows\Fonts\arial.ttf', 8),
]

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


def render(font, ch):
    try:
        m = font.getmask(ch, mode='1')
    except Exception:
        return None
    w, h = m.size
    if w <= 0 or h <= 0 or w > CELL or h > CELL:
        return None
    bm = [[0] * CELL for _ in range(CELL)]
    ox = (CELL - w) // 2
    oy = CELL - h
    for y in range(h):
        for x in range(w):
            if m.getpixel((x, y)):
                bm[oy + y][ox + x] = 1
    return bm


fonts = []
for p, s in FONTS:
    if os.path.isfile(p):
        try:
            fonts.append((p, ImageFont.truetype(p, s)))
        except Exception:
            pass

# collect candidates per codepoint
cands = {}
for ch in needed:
    variants = []
    for name, f in fonts:
        bm = render(f, ch)
        if bm:
            variants.append((sum(sum(r) for r in bm), bm, name))
    if variants:
        variants.sort(key=lambda v: -v[0])
        cands[ch] = variants[0]

# greedy selection maximizing distinctness and ink
chosen = {}
used_sigs = {}
for ch in sorted(cands, key=lambda c: -cands[c][0]):
    ink, bm, name = cands[ch]
    sig = tuple(tuple(r) for r in bm)
    if sig in used_sigs:
        # try another font until the bitmap is distinct
        pick = None
        for name2, f2 in fonts:
            bm2 = render(f2, ch)
            if bm2 and tuple(tuple(r) for r in bm2) not in used_sigs:
                pick = (sum(sum(r) for r in bm2), bm2, name2)
                break
        if pick:
            ink, bm, name = pick
            sig = tuple(tuple(r) for r in bm)
    chosen[ch] = bm
    used_sigs[sig] = ch

dups = {}
for ch, bm in chosen.items():
    sig = tuple(tuple(r) for r in bm)
    dups.setdefault(sig, []).append(ch)
ndup = sum(1 for v in dups.values() if len(v) > 1)
faint = sum(1 for bm in chosen.values() if sum(sum(r) for r in bm) <= 2)

print('glyphs      : %d' % len(chosen))
print('distinct    : %d' % len(dups))
print('duplicates  : %d' % ndup)
print('faint (<=2) : %d' % faint)

json.dump({'%04X' % ord(k): v for k, v in chosen.items()},
          open(os.path.join(WORK, 'data', 'arabic_bitmaps.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote data/arabic_bitmaps.json')