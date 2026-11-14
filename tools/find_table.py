# -*- coding: utf-8 -*-
"""Locate the message table by structural signature.

A message = u16 codes, 0x2000 separates textboxes, 0x8000 terminates.
Signature used: box 2 of campaign message 0 repeats the first word ("JUNGLE"),
so the 6 codes that open a message equal the 6 codes that open its second box.
"""
import os
import struct

ARC = r'C:\Users\user\Desktop\m x4\_work_ar\arc'


def blocks(codes):
    """Yield (start, end) of 0x8000-terminated messages as index ranges."""
    out = []
    start = 0
    for i, c in enumerate(codes):
        if c & 0x8000:
            out.append((start, i + 1))
            start = i + 1
        elif c & 0x2000:
            # box break: keep message open, but mark
            pass
    return out


def box_starts(codes, s, e):
    starts = [s]
    for i in range(s, e):
        if codes[i] & 0x2000:
            starts.append(i + 1)
    return starts


hits = []
for dirpath, _, files in os.walk(ARC):
    for f in sorted(files):
        if not f.endswith('.bin'):
            continue
        p = os.path.join(dirpath, f)
        data = open(p, 'rb').read()
        n = len(data) // 2
        if n < 16:
            continue
        codes = struct.unpack('<%dH' % n, data[:n * 2])
        for (s, e) in blocks(codes):
            bs = box_starts(codes, s, e)
            if len(bs) < 2:
                continue
            b0 = bs[0]
            b1 = bs[1]
            if b1 + 6 > e:
                continue
            w0 = codes[b0:b0 + 6]
            w1 = codes[b1:b1 + 6]
            if w0 == w1 and any(w0):
                hits.append((p, s, e, len(bs), e - s, tuple(w0)))

print('signature hits:', len(hits))
for p, s, e, nboxes, length, w in hits[:25]:
    print('  %s off=0x%06X len=%d boxes=%d head=%s'
          % (os.path.relpath(p, ARC), s * 2, length, nboxes,
             ' '.join('%04X' % c for c in w)))