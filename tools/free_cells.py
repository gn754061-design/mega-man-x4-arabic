# -*- coding: utf-8 -*-
"""Count used vs blank 8x8 cells in the dialogue atlas (256x256, 4bpp, 32x32 grid)."""
P = r'./_work_ar\arc\LOAD_U\00010001.bin'
blob = open(P, 'rb').read()
W = H = 256
px = bytearray(W * H)
for i in range(W * H):
    b = blob[i // 2]
    px[i] = (b >> 4) if (i % 2 == 0) else (b & 0x0F)

cw = ch = 8
cols = rows = 32
used = []
blank = []
for cy in range(rows):
    for cx in range(cols):
        idx = cy * cols + cx
        s = 0
        for y in range(ch):
            base = (cy * ch + y) * W + cx * cw
            for x in range(cw):
                s |= px[base + x]
        (used if s else blank).append(idx)

print('grid        : %dx%d cells of %dx%d px' % (cols, rows, cw, ch))
print('total cells : %d' % (cols * rows))
print('used        : %d' % len(used))
print('blank/free  : %d' % len(blank))
print()
print('max used code : 0x%03X' % max(used))
print('used in 0x000-0x1FF : %d / 512' % len([i for i in used if i < 0x200]))
print('blank in 0x000-0x1FF: %d / 512' % len([i for i in blank if i < 0x200]))
print('blank in 0x200-0x3FF: %d / 512' % len([i for i in blank if i >= 0x200]))
print()
print('first 40 blank codes:', ' '.join('%03X' % i for i in blank[:40]))
print('last 20 blank codes :', ' '.join('%03X' % i for i in blank[-20:]))

# contiguous free ranges
ranges = []
start = prev = None
for i in blank:
    if start is None:
        start = prev = i
    elif i == prev + 1:
        prev = i
    else:
        ranges.append((start, prev))
        start = prev = i
if start is not None:
    ranges.append((start, prev))
print()
print('contiguous free ranges (first 15):')
for a, b in ranges[:15]:
    print('   0x%03X - 0x%03X  (%d cells)' % (a, b, b - a + 1))