# -*- coding: utf-8 -*-
"""Known-plaintext search: ASCII text stored as u16 code units."""
import re
import struct

ISO = "./_work_ar/"disc\disc.iso'
FILES = "./_work_ar/"disc\files.txt'
USER = 2048

files = []
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        files.append((p[0], int(p[1]), int(p[2])))


def owner(lba):
    best = ('?', -1)
    for name, l, size in files:
        if l <= lba and lba < l + (size + USER - 1) // USER and l > best[1]:
            best = (name, l)
    return best[0]


data = open(ISO, 'rb').read()
print('iso bytes:', len(data))


def u16pat(s, base=0):
    return b''.join(struct.pack('<H', base + ord(c)) for c in s)


for word, base in [('JUNGLE', 0), ('JUNGLE', 0x20), ('Repliforce', 0),
                   ('Maverick', 0), ('Infiltrate', 0), ('DR. LIGHT', 0),
                   ('JUNGLE', 0x1000)]:
    pat = u16pat(word, base)
    hits = [m.start() for m in re.finditer(re.escape(pat), data)]
    print('\n%-12s base=0x%04X : %d hit(s)' % (word, base, len(hits)))
    for h in hits[:4]:
        lba = h // USER
        print('   off 0x%08X lba %d %s' % (h, lba, owner(lba)))
        ctx = data[max(0, h - 32):h + 96]
        codes = struct.unpack('<%dH' % (len(ctx) // 2), ctx[:len(ctx) // 2 * 2])
        print('   u16:', ' '.join('%04X' % c for c in codes[:40]))