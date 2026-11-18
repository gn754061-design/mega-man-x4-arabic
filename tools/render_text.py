# -*- coding: utf-8 -*-
"""Reference renderer: reproduce what the game's text engine would draw.

Uses the same inputs the game uses:
  - the dialogue atlas (LOAD_U / 0x10001) after patching
  - the message code streams
  - the engine's rules: 8x8 cells, 20 columns per line, 3 lines per textbox,
    word wrap at word-end marks (0x1000), page break at 0x2000.

Outputs PNG sheets and mechanical layout checks.
"""
import json
import os
import struct

from PIL import Image

WORK = "./_work_ar"'
OUT = os.path.join(WORK, 'out', 'render')
os.makedirs(OUT, exist_ok=True)

USER = 2048
COLS = 32
CELL = 8
ATLAS_W = 256
BOX_COLS = 20
BOX_ROWS = 3

ents = {}
for line in open(os.path.join(WORK, 'disc', 'files.txt'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        ents[p[0]] = (int(p[1]), int(p[2]))

patched = open(os.path.join(WORK, 'out', 'Megaman X4 (Arabic).bin'), 'rb').read()


def arc_blob(name):
    lba, size = ents[name]
    out = bytearray()
    got, sec = 0, lba
    while got < size:
        out += patched[sec * 2352 + 24: sec * 2352 + 24 + USER]
        got += USER
        sec += 1
    return bytes(out[:size])


def member(blob, idx):
    count = struct.unpack('<I', blob[:4])[0]
    off = 0x800
    for i in range(count):
        if i == 0:
            t, s = struct.unpack('<II', blob[8:16])
        else:
            t, s = struct.unpack('<II', blob[0x10 + (i - 1) * 8:0x18 + (i - 1) * 8])
        if i == idx:
            return blob[off:off + s]
        off += s
        if s % 0x800:
            off += 0x800 - (s % 0x800)
    return None


atlas = member(arc_blob('ARC/LOAD_U.ARC'), 1)
m00 = member(arc_blob('ARC/PL00_U.ARC'), 15)
m01 = member(arc_blob('ARC/PL01_U.ARC'), 15)


def cell_bits(code):
    cx = (code % COLS) * CELL
    cy = (code // COLS) * CELL
    rows = []
    for y in range(CELL):
        v = 0
        for x in range(CELL):
            i = (cy + y) * ATLAS_W + (cx + x)
            b = atlas[i // 2]
            px = (b >> 4) if i % 2 == 0 else (b & 0x0F)
            if px:
                v |= 0x80 >> x
        rows.append(v)
    return rows


def parse_messages(blob):
    count = struct.unpack('<H', blob[:2])[0] // 2
    offs = list(struct.unpack('<%dH' % count, blob[:count * 2]))
    out = []
    for i, off in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(blob)
        n = (end - off) // 2
        out.append(struct.unpack('<%dH' % n, blob[off:off + n * 2]))
    return out


def split_pages(codes):
    pages = [[]]
    for c in codes:
        if c & 0x8000:
            break
        if c & 0x2000:
            if pages[-1]:
                pages.append([])
            continue
        g = c & 0x7FF
        if g:
            pages[-1].append(g)
    if not pages[-1]:
        pages.pop()
    return pages or [[]]


def wrap(glyphs):
    """Greedy word wrap at 20 cells; a word is a run of non-space glyphs."""
    lines = []
    cur = []
    word = []
    for g in glyphs:
        if g == 0x1FF:
            if word:
                if len(cur) + len(word) > BOX_COLS and cur:
                    lines.append(cur)
                    cur = []
                cur.extend(word)
                word = []
            if len(cur) >= BOX_COLS:
                lines.append(cur)
                cur = []
            continue
        word.append(g)
        if len(word) > BOX_COLS:
            # a single word longer than the box: hard break it
            if cur:
                lines.append(cur)
                cur = []
            while len(word) > BOX_COLS:
                lines.append(word[:BOX_COLS])
                word = word[BOX_COLS:]
    if word:
        if len(cur) + len(word) > BOX_COLS and cur:
            lines.append(cur)
            cur = []
        cur.extend(word)
    if cur:
        lines.append(cur)
    return lines or [[]]


def render_page(glyphs, scale=3):
    lines = wrap(glyphs)[:BOX_ROWS]
    w = BOX_COLS * CELL
    h = BOX_ROWS * CELL
    img = Image.new('L', (w, h), 0)
    px = img.load()
    for li, line in enumerate(lines):
        for ci, g in enumerate(line[:BOX_COLS]):
            rows = cell_bits(g)
            for y in range(CELL):
                for x in range(CELL):
                    if rows[y] & (0x80 >> x):
                        px[ci * CELL + x, li * CELL + y] = 255
    return img.resize((w * scale, h * scale), Image.NEAREST), len(lines), max(len(l) for l in lines)


def main():
    enc = json.load(open(os.path.join(WORK, 'data', 'arabic_encode.json'), encoding='utf-8'))
    ids = [m['id'] for m in enc['messages']]

    stats = []
    for blob, prefix, label in [(m00, 'dialogue.x.', 'X'), (m01, 'dialogue.zero.', 'Z')]:
        msgs = parse_messages(blob)
        for i, codes in enumerate(msgs):
            eid = '%s%03d' % (prefix, i)
            pages = split_pages(codes)
            mx = 0
            total_lines = 0
            for p in pages:
                _, nl, mw = render_page(p, 1)
                mx = max(mx, mw)
                total_lines += nl
            stats.append((eid, len(pages), total_lines, mx))
            if i < 6:
                sheet = Image.new('L', (BOX_COLS * CELL * 3, BOX_ROWS * CELL * 3 * len(pages)), 0)
                y = 0
                for p in pages:
                    im, _, _ = render_page(p, 3)
                    sheet.paste(im, (0, y))
                    y += im.height
                sheet.save(os.path.join(OUT, '%s.png' % eid))

    print('messages rendered : %d' % len(stats))
    print('pages total       : %d' % sum(s[1] for s in stats))
    print('max line width    : %d cells (limit %d)' % (max(s[3] for s in stats), BOX_COLS))
    over = [s for s in stats if s[3] > BOX_COLS]
    print('lines exceeding   : %d' % len(over))
    empt = [s for s in stats if s[2] == 0]
    print('empty messages    : %d' % len(empt))
    print()
    print('sample renders -> %s' % OUT)
    for f in sorted(os.listdir(OUT))[:8]:
        print('   ', f)

if __name__ == '__main__':
    main()
