# -*- coding: utf-8 -*-
"""
Simulate in-game PS1 dialogue rendering using the patched atlas and native RTL engine.
"""
import os
import struct
from PIL import Image

BASE_DIR = "./_work_ar"'
ATLAS_PATH = os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001.bin')
PL00_PATH = os.path.join(BASE_DIR, 'arc', 'PL00_U', '00000015.bin')
OUT_DIR = os.path.join(BASE_DIR, 'out', 'simulated_scenes')
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Decode 4bpp 16x16 tiles from patched atlas
atlas = open(ATLAS_PATH, 'rb').read()

tiles = {}
for code in range(256):
    tx = code & 0x0F
    ty = (code >> 4) & 0x0F
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        ay = ty * 16 + y
        row_off = ay * 128
        for x in range(16):
            ax = tx * 16 + x
            b = atlas[row_off + (ax // 2)]
            v = (b & 0x0F) if ax % 2 == 0 else (b >> 4)
            if v > 0:
                gray = int((v / 15.0) * 255)
                im.putpixel((x, y), (gray, gray, gray, 255))
    tiles[code] = im

# 2. Render simulated textbox with native RTL engine
def render_box_rtl(codes, title=""):
    box = Image.new('RGBA', (256, 76), (0, 0, 0, 0))
    # Fill inner blue gradient (MMX4 textbox color)
    for y in range(4, 72):
        t = y / 72.0
        r, g, b = 0, int(25 + 35 * t), int(70 + 70 * t)
        for x in range(4, 252):
            box.putpixel((x, y), (r, g, b, 240))
    
    # White border
    for x in range(3, 253):
        box.putpixel((x, 3), (255, 255, 255, 255))
        box.putpixel((x, 72), (255, 255, 255, 255))
        box.putpixel((x, 5), (100, 180, 255, 255))
        box.putpixel((x, 70), (100, 180, 255, 255))
    for y in range(3, 73):
        box.putpixel((3, y), (255, 255, 255, 255))
        box.putpixel((252, y), (255, 255, 255, 255))
        box.putpixel((5, y), (100, 180, 255, 255))
        box.putpixel((250, y), (100, 180, 255, 255))
        
    # In native RTL engine:
    # baseX is 236 (column 19 on the right edge)
    # curX steps by -12
    baseX = 236
    baseY = 8
    curX = baseX
    curY = baseY
    
    for c in codes:
        glyph = c & 0xFF
        if glyph != 0xFF and glyph in tiles:
            box.paste(tiles[glyph], (curX, curY), mask=tiles[glyph])
        
        # Check line break flag
        if c & 0x4000:
            curX = baseX
            curY += 18
        elif c & 0x2000 or c & 0x8000:
            break
        else:
            curX -= 12
            
    return box

# Load messages
data = open(PL00_PATH, 'rb').read()
first_off = struct.unpack('<H', data[:2])[0]
n_msgs = first_off // 2
offsets = [struct.unpack('<H', data[i*2:i*2+2])[0] for i in range(n_msgs)]

# Render Msg 30 (the intro dialogue tested by user)
for mi in [0, 1, 30]:
    start = offsets[mi]
    end = offsets[mi+1] if mi+1 < n_msgs else len(data)
    u16s = [struct.unpack('<H', data[j:j+2])[0] for j in range(start, end, 2)]
    
    # Split into pages
    pages = []
    cur_page = []
    for w in u16s:
        cur_page.append(w)
        if w & 0x2000 or w & 0x8000:
            pages.append(cur_page)
            cur_page = []
    if cur_page:
        pages.append(cur_page)
        
    for pi, page_codes in enumerate(pages):
        img = render_box_rtl(page_codes, f"Msg {mi} Page {pi}")
        out_file = os.path.join(OUT_DIR, f"simulated_rtl_msg{mi:02d}_p{pi:02d}.png")
        img.save(out_file)
        print(f"Saved {out_file}")

print('\nSimulation complete!')
