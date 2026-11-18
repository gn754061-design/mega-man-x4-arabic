# -*- coding: utf-8 -*-
"""Build Arabic glyphs into the MMX4 dialogue atlas and encode Arabic messages.

Stages
  1. reshape logical Arabic -> presentation-form codepoints (arabic_reshaper)
  2. render each needed form at 8x8 from a system Arabic TTF
  3. write glyphs into free atlas cells starting at 0x200
  4. encode each message as u16 codes and rewrite the ARC member
"""
import json
import os
import struct
import sys

import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont

ARC = "./_work_ar/"arc'
WORK = "./_work_ar"'
FONT = r'C:\Windows\Fonts\arial.ttf'
CAT = "./_work_ar/"out\ar_catalog.json'

CELL = 8
COLS = 32
ATLAS_W = ATLAS_H = 256
BASE_CELL = 0x200

END, BOX, EOL, COL, MASK = 0x8000, 0x2000, 0x1000, 0x0800, 0x07FF

# ---------------------------------------------------------------- atlas i/o
at_path = os.path.join(ARC, 'LOAD_U', '00010001.bin')
at = bytearray(open(at_path, 'rb').read())


def px_at(x, y):
    i = y * ATLAS_W + x
    b = at[i // 2]
    return (b >> 4) if i % 2 == 0 else (b & 0x0F)


def set_px(x, y, v):
    i = y * ATLAS_W + x
    if i % 2 == 0:
        at[i // 2] = (at[i // 2] & 0x0F) | (v << 4)
    else:
        at[i // 2] = (at[i // 2] & 0xF0) | (v & 0x0F)


# ink index: most common non-zero value in already-used cells
hist = {}
for i in range(0, len(at)):
    b = at[i]
    for v in (b >> 4, b & 0x0F):
        if v:
            hist[v] = hist.get(v, 0) + 1
INK = max(hist, key=hist.get)
print('ink index = 0x%X (hist %s)' % (INK, sorted(hist.items(), key=lambda kv: -kv[1])[:4]))

# ---------------------------------------------------------------- glyph set
reshaper = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': True, 'support_ligatures': True})

cat = json.load(open(CAT, encoding='utf-8'))
entries = cat['entries']

needed = set()
for e in entries:
    t = e.get('translation', '')
    if not t.strip():
        continue
    for line in t.replace('\f', '\n').split('\n'):
        if not line.strip():
            continue
        shaped = reshaper.reshape(line)
        for ch in shaped:
            needed.add(ch)
print('distinct shaped codepoints:', len(needed))

# ---------------------------------------------------------------- render
font = ImageFont.truetype(FONT, 8)
mapping = {}
bitmaps = {}

for ch in sorted(needed):
    if ch == ' ':
        continue
    img = Image.new('L', (16, 16), 0)
    d = ImageDraw.Draw(img)
    try:
        d.text((2, 0), ch, fill=255, font=font)
    except Exception:
        continue
    bbox = img.getbbox()
    if not bbox:
        continue
    img = img.crop(bbox)
    if img.width > CELL or img.height > CELL:
        # downscale to fit the 8x8 cell
        img = img.resize((min(CELL, img.width), min(CELL, img.height)), Image.LANCZOS)
    gw, gh = img.size
    bm = [[0] * CELL for _ in range(CELL)]
    px = img.load()
    ox = (CELL - gw) // 2
    oy = CELL - gh          # sit on the baseline
    for y in range(gh):
        for x in range(gw):
            if px[x, y] > 96:
                bm[oy + y][ox + x] = 1
    bitmaps[ch] = bm

print('rendered glyphs:', len(bitmaps))

# ---------------------------------------------------------------- place
placed = {}
next_cell = BASE_CELL
for ch in sorted(bitmaps):
    if next_cell >= BASE_CELL + 0x1F0:
        print('!! out of atlas room at 0x%03X' % next_cell)
        break
    placed[ch] = next_cell
    cx = (next_cell % COLS) * CELL
    cy = (next_cell // COLS) * CELL
    bm = bitmaps[ch]
    for y in range(CELL):
        for x in range(CELL):
            set_px(cx + x, cy + y, INK if bm[y][x] else 0)
    next_cell += 1

print('placed %d glyphs at 0x%03X..0x%03X' % (len(placed), BASE_CELL, next_cell - 1))

open(at_path, 'wb').write(bytes(at))
print('atlas written:', at_path, len(at), 'bytes')

# ---------------------------------------------------------------- encoder
def encode(text, sp_code=0x1FF):
    """Encode one message.

    '\\f' is a textbox page break -> 0x2000 code (structure preserved).
    '\\n' is a soft line break -> not emitted; the engine re-wraps at word ends.
    Each line is reshaped, then reversed to visual RTL order.
    """
    codes = []
    pages = text.replace('\r', '').split('\f')
    for pi, page in enumerate(pages):
        for line in page.split('\n'):
            if not line.strip():
                continue
            shaped = reshaper.reshape(line)
            vis = shaped[::-1]
            for ch in vis:
                if ch == ' ':
                    codes.append(sp_code | COL)
                elif ch in placed:
                    codes.append(placed[ch] | COL)
                else:
                    codes.append(sp_code | COL)
            if codes:
                codes[-1] |= EOL        # word/line end marker
        if pi != len(pages) - 1:
            codes.append(BOX)           # textbox page break
    return codes


out_entries = []
missing = set()
for e in entries:
    t = e.get('translation', '')
    if not t.strip():
        out_entries.append({'id': e['id'], 'codes': []})
        continue
    codes = encode(t)
    out_entries.append({'id': e['id'], 'codes': codes})
    for line in t.replace('\f', '\n').split('\n'):
        for ch in reshaper.reshape(line)[::-1]:
            if ch != ' ' and ch not in placed:
                missing.add(ch)

print('messages encoded:', len(out_entries))
print('unmapped shaped codepoints:', sorted('%04X' % ord(c) for c in missing)[:20])

json.dump({'base_cell': BASE_CELL, 'ink': INK,
           'placed': {'%04X' % ord(k): v for k, v in placed.items()},
           'messages': out_entries},
          open(os.path.join(WORK, 'data', 'arabic_encode.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote data/arabic_encode.json')

print()
print('sample:', out_entries[0]['id'], ' '.join('%04X' % c for c in out_entries[0]['codes'][:16]))