# -*- coding: utf-8 -*-
"""Probe ARC container layout and look for compression signatures."""
import math
import os
import struct

EX = r'./_work_ar\disc\extracted'
FILES = r'./_work_ar\disc\files.txt'
ISO = r'./_work_ar\disc\disc.iso'
USER = 2048


def entropy(b):
    if not b:
        return 0.0
    freq = [0] * 256
    for x in b:
        freq[x] += 1
    n = len(b)
    e = 0.0
    for f in freq:
        if f:
            p = f / n
            e -= p * math.log2(p)
    return e


entries = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        entries[p[0]] = (int(p[1]), int(p[2]))

iso = open(ISO, 'rb')

targets = ['ARC/LOAD_U.ARC', 'ARC/FONT8X8.ARC', 'ARC/MOJIPAT.ARC', 'ARC/CAPCOM.ARC',
           'ARC/PL00SEP.ARC', 'ARC/ST0F_U1.ARC']

for name in targets:
    lba, size = entries[name]
    iso.seek(lba * USER)
    blob = iso.read(size)
    print('=' * 70)
    print('%s  size=%d' % (name, len(blob)))
    u32 = struct.unpack('<%dI' % (min(64, len(blob)) // 4), blob[:min(64, len(blob)) // 4 * 4])
    print('  u32[0..15]:', ' '.join('%08X' % v for v in u32[:16]))
    print('  entropy    : %.3f' % entropy(blob))
    # look for common compression magics
    for magic, label in [(b'\x1f\x8b', 'gzip'), (b'PK\x03\x04', 'zip'),
                         (b'\x28\xb5\x2f\xfd', 'zstd'), (b'LZ', 'LZ'),
                         (b'Yay0', 'Yay0'), (b'CRI', 'CRI')]:
        idx = blob.find(magic)
        if idx >= 0:
            print('  magic %-6s at 0x%X' % (label, idx))
    # dump first bytes after likely header
    print('  bytes 0..48:', blob[:48].hex(' '))