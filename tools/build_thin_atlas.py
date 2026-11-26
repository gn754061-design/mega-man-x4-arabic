# -*- coding: utf-8 -*-
"""
Build crisp, thin, retro-authentic Arabic font atlas for Mega Man X4.
- Preserves 100% of the original English font (0x40..0x8D) so Save/Options/Menus are never corrupted.
- Uses Tahoma Regular (size 10) for slender 1-2px strokes and sharp dots.
- Places Kashida strictly on baseline row 10, preventing dot clumping.
- Employs correct PS1 nibble packing (even x in high nibble, odd x in low nibble).
"""
import os
import json
import struct
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper

BASE_DIR = r'./_work_ar'
CAT_PATH = os.path.join(BASE_DIR, 'out', 'ar_catalog.json')
ORIG_ATLAS = os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001_orig.bin')
OUT_ATLAS = os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001.bin')

# 1. Collect needed Arabic glyphs
cat = json.load(open(CAT_PATH, encoding='utf-8'))
reshaper = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': True, 'support_ligatures': True})

needed_chars = set()
for e in cat['entries']:
    t = e.get('translation', '')
    if t == '{glyph:38}':
        continue
    for page in t.split('\f'):
        for line in page.split('\n'):
            for ch in reshaper.reshape(line.strip()):
                if ord(ch) > 127 or ch in '،؟':
                    needed_chars.add(ch)

char_list = sorted(list(needed_chars))
print(f'Total distinct Arabic characters: {len(char_list)}')

# Safe tile codes (outside English range 0x40..0x8D):
# Range 1: 0x8E..0xFE (113 tiles)
# Range 2: 0x39..0x3F (7 tiles)
safe_codes = list(range(0x8E, 0xFF)) + list(range(0x39, 0x40))
assert len(char_list) <= len(safe_codes), f'Too many glyphs: {len(char_list)} > {len(safe_codes)}'

char_to_code = {}
code_to_char = {}
for i, ch in enumerate(char_list):
    code = safe_codes[i]
    char_to_code[ch] = code
    code_to_char[code] = ch

# English digits and punctuation mapping
char_to_code['0'] = 0x40
char_to_code['1'] = 0x41
char_to_code['2'] = 0x42
char_to_code['3'] = 0x43
char_to_code['4'] = 0x44
char_to_code['5'] = 0x45
char_to_code['6'] = 0x46
char_to_code['7'] = 0x47
char_to_code['8'] = 0x48
char_to_code['9'] = 0x49
char_to_code['!'] = 0x87
char_to_code['.'] = 0x86
char_to_code[':'] = 0x89
char_to_code['-'] = 0x84
char_to_code['('] = 0x81
char_to_code[')'] = 0x82
char_to_code[' '] = 0x1FF

# Verify no conflict with English range
for ch in char_list:
    c = char_to_code[ch]
    assert not (0x40 <= c <= 0x8D), f'Conflict with English at {hex(c)} for {ch}'

print('Code mapping verified: 0x40..0x8D is 100% reserved for English!')

# 2. Render Font Atlas at 16x16 with crisp slender strokes
# Start from fresh original atlas
atlas_bytes = bytearray(open(ORIG_ATLAS, 'rb').read())
font = ImageFont.truetype('C:/Windows/Fonts/tahoma.ttf', 10)

preview_grid = Image.new('L', (256, 256), 0)

for ch in char_list:
    code = char_to_code[ch]
    tx = code % 16
    ty = code // 16
    
    name = unicodedata.name(ch, '')
    is_initial = 'INITIAL' in name
    is_medial = 'MEDIAL' in name
    is_final = 'FINAL' in name
    
    connect_left = is_initial or is_medial
    connect_right = is_final or is_medial
    
    im = Image.new('L', (16, 16), 0)
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), ch, font=font)
    bw = bb[2] - bb[0]
    bh = bb[3] - bb[1]
    
    # Horizontal centering in 12px active cell (0..11)
    ox = max(0, (12 - bw) // 2)
    # Baseline at row 10
    oy = max(0, 10 - bb[3])
    d.text((ox - bb[0], oy), ch, fill=255, font=font)
    
    # Refined 1-row Kashida stroke on row 10 only (never row 11)
    if connect_left:
        for x in range(0, max(ox + 2, 5)):
            im.putpixel((x, 10), 255)
    if connect_right:
        for x in range(min(ox + bw - 2, 7), 13):
            im.putpixel((x, 10), 255)
            
    preview_grid.paste(im, (tx * 16, ty * 16))
    
    # Write to 4bpp atlas:
    # High nibble = even x (x % 2 == 0)
    # Low nibble  = odd x  (x % 2 == 1)
    for y in range(16):
        ay = ty * 16 + y
        row_offset = ay * 128
        for x in range(0, 16, 2):
            ax = tx * 16 + x
            v_even = im.getpixel((x, y))
            v_odd  = im.getpixel((x + 1, y))
            
            # Map intensity to palette values
            def to_pal(val):
                if val > 160: return 14 # Solid bright core (0x0E)
                if val > 90:  return 11 # Antialiasing edge (0x0B)
                if val > 30:  return 8  # Subtle outer edge (0x08)
                return 0
                
            n_hi = to_pal(v_even)
            n_lo = to_pal(v_odd)
            
            byte_val = (n_hi << 4) | (n_lo & 0x0F)
            atlas_bytes[row_offset + (ax // 2)] = byte_val

open(OUT_ATLAS, 'wb').write(bytes(atlas_bytes))
preview_grid.save(os.path.join(BASE_DIR, 'out', 'thin_atlas_preview.png'))
print(f'Successfully built clean atlas to {OUT_ATLAS} and saved thin_atlas_preview.png!')
