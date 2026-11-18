# -*- coding: utf-8 -*-
"""Locate text/font data in the extracted disc image."""
import os
import re
import sys

ISO = "./_work_ar/"disc\disc.iso'
USER = 2048
FILES = "./_work_ar/"disc\files.txt'

files = []
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        files.append((p[0], int(p[1]), int(p[2])))


def owner(lba):
    best = ('?', -1)
    for name, l, size in files:
        if l <= lba and lba < l + (size + USER - 1) // USER:
            if l > best[1]:
                best = (name, l)
    return best[0]


data = open(ISO, 'rb').read()
print('iso bytes:', len(data))

for needle in [b'JUNGLE', b'Repliforce', b'Maverick', b'DR. LIGHT', b'Light Web']:
    hits = [m.start() for m in re.finditer(re.escape(needle), data)]
    print('\n%s : %d hit(s)' % (needle.decode(), len(hits)))
    for h in hits[:6]:
        lba = h // USER
        print('   off 0x%08X  lba %d  %s' % (h, lba, owner(lba)))
        ctx = data[max(0, h - 40):h + 80]
        print('      ', repr(ctx))