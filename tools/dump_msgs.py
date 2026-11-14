# -*- coding: utf-8 -*-
"""Dump message records from the located text member and align with known English."""
import struct
import sys

P = r'C:\Users\user\Desktop\m x4\_work_ar\arc\PL00_U\00000015.bin'
data = open(P, 'rb').read()
n = len(data) // 2
codes = struct.unpack('<%dH' % n, data[:n * 2])
print('member bytes:', len(data), 'codes:', n)
print('min code: 0x%04X  max code: 0x%04X' % (min(codes), max(codes)))

# split into messages on 0x8000
msgs = []
start = 0
for i, c in enumerate(codes):
    if c & 0x8000:
        msgs.append((start, i + 1))
        start = i + 1
print('messages:', len(msgs))
print()

for k, (s, e) in enumerate(msgs[:6]):
    seg = codes[s:e]
    print('--- msg %d  off=0x%06X  len=%d' % (k, s * 2, len(seg)))
    print('   codes:', ' '.join('%03X' % (c & 0x1FFF) for c in seg))
    print('   raw  :', ' '.join('%04X' % c for c in seg))
    print()

print('=== distribution of low-13-bit codes ===')
import collections
lo = collections.Counter(c & 0x1FFF for c in codes)
print('distinct low codes:', len(lo))
print('top 25:', [(hex(c), k) for c, k in lo.most_common(25)])
hi = collections.Counter(c & 0xE000 for c in codes)
print('high-bit groups:', [(hex(c), k) for c, k in hi.most_common(10)])