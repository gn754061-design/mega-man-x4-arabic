# -*- coding: utf-8 -*-
"""Final Arabic glyph build: 1-bit trado.ttf bitmaps -> atlas -> message encoding."""
import json
import os
import struct

import arabic_reshaper

WORK = r'./_work_ar'
ATLAS = os.path.join(WORK, 'arc', 'LOAD_U', '00010001.bin')

CELL = 8
COLS = 32
ATLAS_W = ATLAS_H = 256
BASE_CELL = 0x200
END, BOX, EOL, COL, MASK = 0x8000, 0x2000, 0x1000, 0x0800, 0x07FF

at = bytearray(open(ATLAS, 'rb').read())


def set_px(x, y, v):
    i = y * ATLAS_W + x
    if i % 2 == 0:
        at[i // 2] = (at[i // 2] & 0x0F) | (v << 4)
    else:
        at[i // 2] = (at[i // 2] & 0xF0) | (v & 0x0F)


hist = {}
for b in at:
    for v in (b >> 4, b & 0x0F):
        if v:
            hist[v] = hist.get(v, 0) + 1
INK = max(hist, key=hist.get)

bitmaps = {int(k, 16): v for k, v in
           json.load(open(os.path.join(WORK, 'data', 'arabic_bitmaps.json'), encoding='utf-8')).items()}
print('loaded bitmaps: %d  (ink=0x%X)' % (len(bitmaps), INK))

reshaper = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': True, 'support_ligatures': True})

cat = json.load(open(os.path.join(WORK, 'out', 'ar_catalog.json'), encoding='utf-8'))

# waw forms are not present at 8px in trado.ttf; alias them to the plain waw
for _a, _b in ((0xFE85, 0xFE8D), (0xFE86, 0xFE8D)):
    if _a not in bitmaps and _b in bitmaps:
        bitmaps[_a] = bitmaps[_b]

placed = {}
cell = BASE_CELL
faint = []
for cp in sorted(bitmaps):
    bm = bitmaps[cp]
    ink = sum(sum(r) for r in bm)
    if cell >= BASE_CELL + 0x1F0:
        print('!! atlas full')
        break
    placed[cp] = cell
    if ink <= 2:
        faint.append((cp, ink))
    cx = (cell % COLS) * CELL
    cy = (cell // COLS) * CELL
    for y in range(CELL):
        for x in range(CELL):
            set_px(cx + x, cy + y, INK if (y < len(bm) and x < len(bm[y]) and bm[y][x]) else 0)
    cell += 1

print('placed %d glyphs at 0x%03X..0x%03X' % (len(placed), BASE_CELL, cell - 1))
print('faint glyphs (ink<=2): %s' % ['U+%04X:%d' % f for f in faint])

open(ATLAS, 'wb').write(bytes(at))
print('atlas written:', len(at), 'bytes')


def encode(text, sp=0x1FF):
    codes = []
    pages = text.replace('\r', '').split('\f')
    for pi, page in enumerate(pages):
        for line in page.split('\n'):
            if not line.strip():
                continue
            vis = reshaper.reshape(line)[::-1]
            for ch in vis:
                if ch == ' ':
                    codes.append(sp | COL)
                elif ord(ch) in placed:
                    codes.append(placed[ord(ch)] | COL)
                else:
                    codes.append(sp | COL)
            if codes:
                codes[-1] |= EOL
        if pi != len(pages) - 1:
            codes.append(BOX)
    return codes


out = []
missing = set()
for e in cat['entries']:
    t = e.get('translation', '')
    if not t.strip():
        out.append({'id': e['id'], 'codes': []})
        continue
    out.append({'id': e['id'], 'codes': encode(t)})
    for line in t.replace('\f', '\n').split('\n'):
        for ch in reshaper.reshape(line)[::-1]:
            if ch != ' ' and ord(ch) not in placed:
                missing.add(ch)

print('messages encoded: %d' % len(out))
print('unmapped: %s' % (['U+%04X' % ord(c) for c in missing] or 'none'))

json.dump({'base_cell': BASE_CELL, 'ink': INK,
           'placed': {'%04X' % k: v for k, v in placed.items()},
           'messages': out},
          open(os.path.join(WORK, 'data', 'arabic_encode.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote data/arabic_encode.json')