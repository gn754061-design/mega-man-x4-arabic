# -*- coding: utf-8 -*-
"""Extract ARC members using the deduced table: count, total, {id,size}[], 0x800-aligned."""
import math
import os
import struct

ISO = "./_work_ar/"disc\disc.iso'
FILES = "./_work_ar/"disc\files.txt'
OUT = "./_work_ar/"arc'
USER = 2048
ALIGN = 0x800


def entropy(b):
    if not b:
        return 0.0
    freq = [0] * 256
    for x in b:
        freq[x] += 1
    n = len(b)
    return -sum((f / n) * math.log2(f / n) for f in freq if f)


entries = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        entries[p[0]] = (int(p[1]), int(p[2]))

iso = open(ISO, 'rb')


def read_member(lba, size):
    iso.seek(lba * USER)
    return iso.read(size)


def dump_arc(name, align=ALIGN):
    lba, size = entries[name]
    blob = read_member(lba, size)
    count, total = struct.unpack('<II', blob[:8])
    print('=' * 72)
    print('%s size=%d count=%d total=0x%X' % (name, size, count, total))
    if count > 64 or count == 0:
        print('  implausible count, skipping')
        return None
    table = []
    for i in range(count):
        mid, msize = struct.unpack('<II', blob[8 + i * 8:16 + i * 8])
        table.append((mid, msize))
    for mid, msize in table:
        print('   id=0x%08X size=0x%X (%d)' % (mid, msize, msize))

    outdir = os.path.join(OUT, name.split('/')[-1].replace('.ARC', ''))
    os.makedirs(outdir, exist_ok=True)
    hdr = 8 + count * 8
    off = (hdr + align - 1) // align * align if align else hdr
    made = []
    for mid, msize in table:
        if off + msize > len(blob):
            print('   !! id=0x%08X overruns (off 0x%X + 0x%X > 0x%X)' % (mid, off, msize, len(blob)))
            break
        data = blob[off:off + msize]
        p = os.path.join(outdir, '%08X.bin' % mid)
        open(p, 'wb').write(data)
        nz = sum(1 for b in data[:4096] if b)
        print('   -> %08X.bin off=0x%06X size=0x%06X entropy=%.2f nonzero=%d/%d'
              % (mid, off, msize, entropy(data), nz, min(4096, len(data))))
        made.append(p)
        off = (off + msize + align - 1) // align * align if align else off + msize
    return made


for n in ['ARC/LOAD_U.ARC', 'ARC/FONT8X8.ARC', 'ARC/CAPCOM.ARC', 'ARC/ST0F_U1.ARC']:
    dump_arc(n)