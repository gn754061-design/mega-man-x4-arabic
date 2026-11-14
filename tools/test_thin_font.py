# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper, unicodedata

f = ImageFont.truetype('C:/Windows/Fonts/tahoma.ttf', 10)
reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': True})

def render_word(word):
    sh = reshaper.reshape(word)
    canvas = Image.new('L', (len(sh) * 12 + 16, 16), 0)
    for i, ch in enumerate(sh):
        im = Image.new('L', (16, 16), 0)
        d = ImageDraw.Draw(im)
        bb = d.textbbox((0, 0), ch, font=f)
        bw = bb[2] - bb[0]
        name = unicodedata.name(ch, '')
        is_init = 'INITIAL' in name
        is_med = 'MEDIAL' in name
        is_fin = 'FINAL' in name
        
        ox = max(0, (12 - bw) // 2)
        oy = max(0, 10 - bb[3]) # baseline at row 10
        d.text((ox - bb[0], oy), ch, fill=255, font=f)
        
        # Single-row Kashida on row 10
        if is_init or is_med:
            for x in range(0, max(ox + 2, 5)):
                im.putpixel((x, 10), 255)
        if is_fin or is_med:
            for x in range(min(ox + bw - 2, 7), 13):
                im.putpixel((x, 10), 255)
                
        # Paste into canvas (RTL: char 0 on right)
        px = canvas.width - (i + 1) * 12
        canvas.paste(im, (px, 0))
    return canvas

for w in ['فهمت', 'طريقي', 'إكس']:
    im = render_word(w)
    print(f'=== Word {w} ===')
    for y in range(3, 14):
        s = ''.join('#' if im.getpixel((x, y)) > 60 else '.' for x in range(im.width))
        if '#' in s:
            print(f'{y:2d}: {s}')
