# -*- coding: utf-8 -*-
"""Template-match dialogue-font letters across every member to find menu text.

If the menus use the same 8x8 font, the bitmaps of N, E, W, G, A, M will appear
as aligned tiles inside the member that stores the menu artwork.
"""
import os

ARC = r'./_work_ar\arc'
ATLAS = os.path.join(ARC, 'LOAD_U', '00010001.bin')
at = open(ATLAS, 'rb').read()
W = 256

# dialogue glyph codes (from the verified codec)
CODES = {'A': 0x4A, 'C': 0x4C, 'E': 0x4E, 'G': 0x50, 'M': 0x56, 'N': 0x57,
         'O': 0x58, 'W': 0x60, 'S': 0x5C, 'T': 0x5D, 'V': 0x5F, 'X': 0x61}


def glyph(code):
    cx = (code % 32) * 8
    cy = (code // 32) * 8
    rows = []
    for y in range(8):
        v = 0
        for x in range(8):
            i = (cy + y) * W + (cx + x)
            b = at[i // 2]
            px = (b >> 4) if i % 2 == 0 else (b & 0x0F)
            if px:
                v |= 0x80 >> x
        rows.append(v)
    return rows


templates = {ch: glyph(c) for ch, c in CODES.items()}
for ch, t in templates.items():
    print('%s: %s' % (ch, ' '.join('%02X' % r for r in t)))

print()


def match_at(px, w, h, x0, y0, tpl):
    for y in range(8):
        base = (y0 + y) * w + x0
        byte = 0
        for x in range(8):
            if px[base + x]:
                byte |= 0x80 >> x
        if byte != tpl[y]:
            return False
    return True


def to_px(blob, w, h):
    need = (w * h) // 2
    if len(blob) < need:
        return None
    px = bytearray(w * h)
    for i in range(w * h):
        b = blob[i // 2]
        px[i] = (b >> 4) if i % 2 == 0 else (b & 0x0F)
    return px


results = []
for dirpath, _, files in os.walk(ARC):
    for f in sorted(files):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(dirpath, f)
        blob = open(p, 'rb').read()
        best = (0, None)
        for w, h in [(256, 256), (320, 240), (128, 256), (512, 256), (256, 512)]:
            px = to_px(blob, w, h)
            if px is None:
                continue
            for ch, tpl in templates.items():
                cnt = 0
                for y0 in range(0, h - 7, 4):
                    for x0 in range(0, w - 7, 4):
                        if match_at(px, w, h, x0, y0, tpl):
                            cnt += 1
                if cnt > best[0]:
                    best = (cnt, (w, h, ch))
        if best[0] >= 3:
            results.append((best[0], p, best[1]))

results.sort(key=lambda r: -r[0])
print('members with >=3 template matches:', len(results))
for cnt, p, (w, h, ch) in results[:15]:
    print('  matches=%4d  %dx%d  letter=%s  %s' % (cnt, w, h, ch, os.path.relpath(p, ARC)))