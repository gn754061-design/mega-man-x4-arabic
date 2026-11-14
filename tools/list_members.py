# -*- coding: utf-8 -*-
"""List every member of the player ARCs with type, size and a text score."""
import os
import struct

ARC = r'C:\Users\user\Desktop\m x4\_work_ar\arc'
KNOWN = set(range(0x40, 0x7E)) | {0x1FF} | set(range(0x83, 0x8C))


def text_score(codes):
    ends = boxes = known = total = 0
    for c in codes:
        if c & 0x8000:
            ends += 1
            continue
        if c & 0x2000:
            boxes += 1
        g = c & 0x7FF
        total += 1
        if g in KNOWN or 0x200 <= g < 0x300:
            known += 1
    if total < 8:
        return 0.0
    return (known / total) * (1 + ends / 50.0)


for arc in ('PL00_U', 'PL01_U', 'PL02_U'):
    d = os.path.join(ARC, arc)
    files = sorted(f for f in os.listdir(d) if f.endswith('.bin'))
    print('=' * 78)
    print('%s : %d members' % (arc, len(files)))
    for f in files:
        data = open(os.path.join(d, f), 'rb').read()
        n = len(data) // 2
        codes = struct.unpack('<%dH' % n, data[:n * 2]) if n else ()
        s = text_score(codes)
        # count plausible text blocks
        blocks = 0
        start = 0
        for i, c in enumerate(codes):
            if c & 0x8000:
                if (i - start) >= 8:
                    blocks += 1
                start = i + 1
        print('   type=%s size=%7d  text_score=%.2f  blocks=%d'
              % (f.split('.')[0], len(data), s, blocks))
    print()