# -*- coding: utf-8 -*-
"""
Build 16x16 live Arabic font atlas and encode Arabic dialogue for Mega Man X4 (PS1).
Features:
  1. 16x16 tile grid (256x256 atlas = 16x16 tiles of 16x16 pixels).
  2. Correct PS1 4bpp nibble order (low nibble at even x, high nibble at odd x).
  3. Proper glyph index mapping in 0x01..0xFE (avoiding wrapping).
  4. Continuous cursive baseline joining (Kashida connection on rows 10-11 for initial, medial, final forms).
  5. Native RTL engine support with right-aligned text starting from the right frame border.
  6. Line breaks (0x4000 flag on last character of lines 1 and 2).
  7. Page breaks (0x2000 flag on last character of page/box).
  8. End-of-message (0x8000 flag on last character of message).
  9. BoxLow (0x0800 flag preserved from original messages).
 10. Automatic digit reversal for proper LTR numbers in Arabic text.
"""
import os
import re
import json
import struct
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper

BASE_DIR = r'C:\Users\user\Desktop\m x4\_work_ar'
CAT_PATH = os.path.join(BASE_DIR, 'out', 'ar_catalog.json')
ORIG_ATLAS = os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001_orig.bin')
OUT_ATLAS = os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001.bin')
ORIG_PL00 = os.path.join(BASE_DIR, 'arc', 'PL00_U', '00000015_orig.bin')
OUT_PL00 = os.path.join(BASE_DIR, 'arc', 'PL00_U', '00000015.bin')
ORIG_PL01 = os.path.join(BASE_DIR, 'arc', 'PL01_U', '00000015_orig.bin')
OUT_PL01 = os.path.join(BASE_DIR, 'arc', 'PL01_U', '00000015.bin')
ORIG_SLUS = os.path.join(BASE_DIR, 'disc', 'extracted', 'SLUS_005.61')
OUT_SLUS = os.path.join(BASE_DIR, 'out', 'SLUS_005.61')

# 1. Load catalog & collect distinct shaped glyphs
cat = json.load(open(CAT_PATH, encoding='utf-8'))
reshaper = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': True, 'support_ligatures': True})

needed_chars = set()
for e in cat['entries']:
    t = e.get('translation', '')
    if not t.strip():
        continue
    for page in t.split('\f'):
        for line in page.split('\n'):
            line = line.strip()
            if not line:
                continue
            for ch in reshaper.reshape(line):
                if ch != ' ':
                    needed_chars.add(ch)

# Extra common characters for complete coverage
extra = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', '-', '(', ')', '"', '%']
for c in extra:
    needed_chars.add(c)

char_list = sorted(list(needed_chars))
print(f'Total distinct glyphs: {len(char_list)}')

# Assign tile codes starting at 0x10 (col 0, row 1)
START_CODE = 0x10
char_to_code = {}
code_to_char = {}
for i, ch in enumerate(char_list):
    code = START_CODE + i
    char_to_code[ch] = code
    code_to_char[code] = ch

print(f'Glyphs mapped to codes 0x{START_CODE:02X}..0x{START_CODE + len(char_list) - 1:02X}')

# Save map
json.dump({f'0x{c:02X}': ch for c, ch in code_to_char.items()},
          open(os.path.join(BASE_DIR, 'out', 'glyph_code_map.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)

# 2. Render Font Atlas at 16x16 with Kashida baseline connection (size 11 for crisp, refined appearance)
atlas_bytes = bytearray(open(ORIG_ATLAS, 'rb').read())
font_path = 'C:/Windows/Fonts/tahomabd.ttf'
font = ImageFont.truetype(font_path, 11)

preview_grid = Image.new('L', (256, 256), 0)

for ch, code in char_to_code.items():
    tx = code & 0x0F
    ty = (code >> 4) & 0x0F
    
    name = unicodedata.name(ch, '')
    is_initial = 'INITIAL' in name
    is_medial = 'MEDIAL' in name
    is_final = 'FINAL' in name
    
    # In RTL rendering:
    # Character 0 is at right (X=108), Character 1 is to its left (X=96).
    # Thus:
    # Next letter in Arabic word is to the LEFT (x=0 of tile). Initial & Medial connect to LEFT.
    # Previous letter in Arabic word is to the RIGHT (x=11..12 of tile). Final & Medial connect to RIGHT.
    connect_left = is_initial or is_medial
    connect_right = is_final or is_medial
    
    # Render glyph on 16x16 canvas
    im = Image.new('L', (16, 16), 0)
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), ch, font=font)
    bw = bb[2] - bb[0]
    bh = bb[3] - bb[1]
    
    # Horizontal centering in 12px active cell (0..11)
    ox = max(0, (12 - bw) // 2)
    # Baseline at row 11
    oy = max(0, 11 - bb[3])
    d.text((ox - bb[0], oy), ch, fill=255, font=font)
    
    # Kashida baseline stroke extension (rows 10 and 11)
    if connect_left:
        for y in (10, 11):
            for x in range(0, max(ox + 2, 6)):
                im.putpixel((x, y), 255 if y == 10 else 200)
    if connect_right:
        for y in (10, 11):
            for x in range(min(ox + bw - 2, 6), 13):
                im.putpixel((x, y), 255 if y == 10 else 200)
    
    preview_grid.paste(im, (tx * 16, ty * 16))
    
    # Write to 4bpp atlas with correct nibble order and antialiasing
    for y in range(16):
        ay = ty * 16 + y
        row_offset = ay * 128
        for x in range(16):
            ax = tx * 16 + x
            intensity = im.getpixel((x, y))
            if intensity > 160:
                val = 14  # Solid bright ink (0x0E)
            elif intensity > 70:
                val = 11  # Antialiasing edge (0x0B)
            elif intensity > 25:
                val = 6   # Outer subtle edge
            else:
                val = 0   # Transparent
            
            byte_idx = row_offset + (ax // 2)
            if ax % 2 == 0:  # Even x: low nibble
                atlas_bytes[byte_idx] = (atlas_bytes[byte_idx] & 0xF0) | (val & 0x0F)
            else:            # Odd x: high nibble
                atlas_bytes[byte_idx] = (atlas_bytes[byte_idx] & 0x0F) | ((val & 0x0F) << 4)

open(OUT_ATLAS, 'wb').write(bytes(atlas_bytes))
preview_grid.save(os.path.join(BASE_DIR, 'out', 'live_atlas_preview.png'))
print('Saved updated LOAD_U/00010001.bin and live_atlas_preview.png')

# 3. Message Encoding Function (Native RTL Order)
def get_original_boxlow(orig_path):
    data = open(orig_path, 'rb').read()
    first_off = struct.unpack('<H', data[:2])[0]
    n_msgs = first_off // 2
    offs = [struct.unpack('<H', data[i*2:i*2+2])[0] for i in range(n_msgs)]
    box_lows = []
    for mi in range(n_msgs):
        start = offs[mi]
        end = offs[mi+1] if mi+1 < n_msgs else len(data)
        bl_list = []
        box_first = True
        for j in range(start, end, 2):
            if j+2 > len(data): break
            w = struct.unpack('<H', data[j:j+2])[0]
            if box_first:
                bl_list.append(bool(w & 0x0800))
                box_first = False
            if w & 0x2000:
                box_first = True
            if w & 0x8000:
                break
        box_lows.append(bl_list)
    return box_lows

x_boxlows = get_original_boxlow(ORIG_PL00)
z_boxlows = get_original_boxlow(ORIG_PL01)

def encode_message_rtl(text, box_low_flags):
    """
    Encode an Arabic message in native RTL order for the RTL-patched engine.
    - Preserves boxLow flag (0x0800).
    - Line break (0x4000) on the last character of each line.
    - Page break (0x2000) on the last character of each page/box.
    - End-of-message (0x8000) on the last character of the message.
    - Reverses embedded digits so they read LTR (e.g. 5567).
    """
    if not text.strip():
        return [0x81FF]
    
    pages = text.split('\f')
    codes = []
    
    for pi, page in enumerate(pages):
        is_low = box_low_flags[pi] if pi < len(box_low_flags) else (box_low_flags[0] if box_low_flags else False)
        base_flag = 0x1800 if is_low else 0x1000
        first_box_flag = 0x0800 if is_low else 0x0000
        
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        if not lines:
            continue
        
        for li, line in enumerate(lines):
            # Reverse embedded digits so they read LTR when drawn RTL
            line_proc = re.sub(r'\d+', lambda m: m.group(0)[::-1], line)
            
            # Reshape Arabic characters in natural reading order
            shaped = reshaper.reshape(line_proc)
            
            is_last_line_in_box = (li == len(lines) - 1)
            is_last_box = (pi == len(pages) - 1)
            
            for ci, ch in enumerate(shaped):
                is_first_in_box = (li == 0 and ci == 0)
                is_last_in_line = (ci == len(shaped) - 1)
                
                if ch == ' ':
                    glyph_code = 0x1FF
                elif ch in char_to_code:
                    glyph_code = char_to_code[ch]
                else:
                    glyph_code = 0x1FF
                
                flags = base_flag
                if is_first_in_box and not (flags & 0x1000):
                    flags |= first_box_flag
                
                if is_last_in_line:
                    if is_last_line_in_box:
                        if is_last_box:
                            flags |= 0x8000  # End of message
                        else:
                            flags |= 0x2000  # Page / box break
                    else:
                        flags |= 0x4000      # Line break
                
                codes.append(flags | (glyph_code & 0x07FF))
                
    return codes

def build_member(entries, boxlow_list, orig_size, out_path):
    n = len(entries)
    msg_code_list = []
    for mi, e in enumerate(entries):
        bl = boxlow_list[mi] if mi < len(boxlow_list) else [False]
        codes = encode_message_rtl(e.get('translation', ''), bl)
        msg_code_list.append(codes)
    
    first_offset = n * 2
    cur_off = first_offset
    offsets = []
    for codes in msg_code_list:
        offsets.append(cur_off)
        cur_off += len(codes) * 2
    
    out_buf = bytearray()
    for off in offsets:
        out_buf.extend(struct.pack('<H', off))
    for codes in msg_code_list:
        for c in codes:
            out_buf.extend(struct.pack('<H', c))
    
    total_len = len(out_buf)
    print(f'{os.path.basename(out_path)}: payload {total_len} bytes, budget limit {orig_size}')
    if total_len > orig_size:
        raise ValueError(f'Overflow: {total_len} > {orig_size}')
    
    out_buf.extend(b'\x00' * (orig_size - total_len))
    open(out_path, 'wb').write(bytes(out_buf))
    print(f'Wrote {out_path} ({len(out_buf)} bytes, {orig_size - total_len} bytes slack remaining)')

# Build X (first 55 entries) and Zero (remaining 49 entries)
x_entries = cat['entries'][:55]
z_entries = cat['entries'][55:]

build_member(x_entries, x_boxlows, 22196, OUT_PL00)
build_member(z_entries, z_boxlows, 15004, OUT_PL01)

# Also copy to out/ for apply_patch.py
open(os.path.join(BASE_DIR, 'out', 'new_PL00_U_00000015.bin'), 'wb').write(open(OUT_PL00, 'rb').read())
open(os.path.join(BASE_DIR, 'out', 'new_PL01_U_00000015.bin'), 'wb').write(open(OUT_PL01, 'rb').read())

# 4. Patch SLUS_005.61 for Native RTL Rendering
slus_data = bytearray(open(ORIG_SLUS, 'rb').read())

# 1. 0x012D74: addiu v0, zero, 108 (0x006C)
slus_data[0x012D74:0x012D78] = bytes([0x6C, 0x00, 0x02, 0x24])
# 2. 0x0137E8: addiu v0, zero, 108 (0x006C)
slus_data[0x0137E8:0x0137EC] = bytes([0x6C, 0x00, 0x02, 0x24])
# 3. 0x013C64: addiu v0, zero, 108 (0x006C)
slus_data[0x013C64:0x013C68] = bytes([0x6C, 0x00, 0x02, 0x24])
# 4. 0x013C80: addiu v0, v0, -12 (0xFFF4)
slus_data[0x013C80:0x013C84] = bytes([0xF4, 0xFF, 0x42, 0x24])

open(OUT_SLUS, 'wb').write(bytes(slus_data))
print(f'Wrote RTL-patched executable to {OUT_SLUS}')

print('\nLive Arabic font, RTL-patched executable, and dialogue members built successfully!')
