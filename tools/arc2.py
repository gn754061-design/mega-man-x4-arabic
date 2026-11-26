# -*- coding: utf-8 -*-
"""Correct ARC parser (TeheManX4_Editor ARC.cs) + text-block scanner (TextEntry.cs)."""
import os
import struct

ISO = r'./_work_ar\disc\disc.iso'
FILES = r'./_work_ar\disc\files.txt'
OUT = r'./_work_ar\arc'
USER = 2048

END_TEXT = 0x8000
END_BOX = 0x2000

entries = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        entries[p[0]] = (int(p[1]), int(p[2]))

iso = open(ISO, 'rb')


def parse_arc(blob):
    if len(blob) < 0x800:
        return None
    count, total = struct.unpack('<II', blob[:8])
    if count == 0 or count > 4096 or total != len(blob):
        return None
    out = []
    for i in range(count):
        if i == 0:
            typ, size = struct.unpack('<II', blob[8:16])
        else:
            typ, size = struct.unpack('<II', blob[0x10 + (i - 1) * 8:0x18 + (i - 1) * 8])
        out.append((typ, size))
    return out


def extract_all():
    os.makedirs(OUT, exist_ok=True)
    report = []
    for name, (lba, size) in sorted(entries.items()):
        if not name.upper().endswith('.ARC'):
            continue
        iso.seek(lba * USER)
        blob = iso.read(size)
        table = parse_arc(blob)
        if table is None:
            report.append((name, None, 0, 0, 0))
            continue
        off = 0x800
        outdir = os.path.join(OUT, name.split('/')[-1][:-4])
        os.makedirs(outdir, exist_ok=True)
        texts = 0
        for i, (typ, msize) in enumerate(table):
            data = blob[off:off + msize]
            if len(data) < msize:
                break
            open(os.path.join(outdir, '%08X.bin' % typ), 'wb').write(data)
            nb = scan_text(data)
            if nb:
                texts += nb
                report.append((name, typ, off, msize, nb))
            off += msize
            if msize % 0x800:
                off += 0x800 - (msize % 0x800)
    return report


def scan_text(data):
    """Count plausible text boxes: u16 stream, terminated by 0x8000, >=1 box-break."""
    if len(data) < 4:
        return 0
    n = len(data) // 2
    codes = struct.unpack('<%dH' % n, data[:n * 2])
    boxes = 0
    i = 0
    while i < n:
        start = i
        has_box = False
        while i < n:
            c = codes[i]
            i += 1
            if c & END_TEXT:
                break
            if c & END_BOX:
                has_box = True
                break
        else:
            break
        length = i - start
        if has_box and 2 <= length <= 64:
            boxes += 1
        elif length <= 1:
            continue
    return boxes


if __name__ == '__main__':
    rep = extract_all()
    hits = [r for r in rep if r[1] is not None]
    hits.sort(key=lambda r: -r[4])
    print('members with text-like boxes: %d' % len(hits))
    for name, typ, off, size, nb in hits[:40]:
        print('  %-22s type=0x%08X off=0x%06X size=0x%06X boxes=%d' % (name, typ, off, size, nb))