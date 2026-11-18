# -*- coding: utf-8 -*-
"""Find text blocks: runs of u16 codes all < 0x0100, containing 0x2000 box breaks."""
import os
import struct

ARC = "./_work_ar/"arc'

results = []
for dirpath, _, files in os.walk(ARC):
    for f in files:
        if not f.endswith('.bin'):
            continue
        p = os.path.join(dirpath, f)
        data = open(p, 'rb').read()
        n = len(data) // 2
        if n < 8:
            continue
        codes = struct.unpack('<%dH' % n, data[:n * 2])
        i = 0
        while i < n:
            if codes[i] >= 0x0100:
                i += 1
                continue
            j = i
            boxes = 0
            ends = 0
            while j < n and codes[j] < 0x0100:
                j += 1
            # run [i, j)
            # count 0x2000 inside
            seg = codes[i:j]
            boxes = seg.count(0x2000)
            if len(seg) >= 12 and boxes >= 1:
                results.append((len(seg), boxes, p, i))
            i = j

results.sort(key=lambda r: -r[0])
print('candidate runs:', len(results))
for length, boxes, p, off in results[:30]:
    print('  len=%4d boxes=%3d off=0x%06X %s' % (length, boxes, off * 2, os.path.relpath(p, ARC)))