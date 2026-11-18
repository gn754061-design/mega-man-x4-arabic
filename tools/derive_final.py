# -*- coding: utf-8 -*-
"""Derive the definitive glyph table by aligning every code against the known plaintext."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decode2 import load, CAT, ARC, TABLE, MASK, BOX, END  # noqa: E402

src = json.load(open(CAT, encoding='utf-8'))
known = {e['id']: e['source'] for e in src['entries']}

mapping = {}
conflict = set()

for label, rel, prefix in [('X', r'PL00_U\00000015.bin', 'dialogue.x.'),
                           ('Zero', r'PL01_U\00000015.bin', 'dialogue.zero.')]:
    p = os.path.join(ARC, rel)
    if not os.path.isfile(p):
        continue
    count, offs, msgs = load(p)
    for i, codes in enumerate(msgs):
        eid = '%s%03d' % (prefix, i)
        exp = known.get(eid)
        if exp is None:
            continue
        want = exp.replace('\n', '').replace('\f', '')
        # walk codes; produce one glyph per non-zero code (box/end carry no char unless glyph!=0)
        gi = 0
        wi = 0
        for c in codes:
            g = c & MASK
            if c & END:
                if g and wi < len(want):
                    if g in mapping and mapping[g] != want[wi]:
                        conflict.add((g, mapping[g], want[wi]))
                    else:
                        mapping[g] = want[wi]
                break
            if g:
                if wi < len(want):
                    ch = want[wi]
                    if g in mapping and mapping[g] != ch:
                        conflict.add((g, mapping[g], ch))
                    else:
                        mapping[g] = ch
                    wi += 1
                else:
                    wi += 1
            if c & BOX:
                wi += 0  # box break already removed from `want`

print('glyphs derived : %d' % len(mapping))
print('conflicts      : %d' % len(conflict))
for c in sorted(conflict)[:10]:
    print('   ', c)

print()
print('=== table ===')
for lo, hi, name in [(0x20, 0x3F, 'punct/digits?'), (0x40, 0x5F, 'digits+upper'),
                     (0x60, 0x7F, 'lower+punct'), (0x80, 0x8F, 'punct2'),
                     (0x1F0, 0x200, 'space')]:
    row = []
    for g in range(lo, hi):
        if g in mapping:
            row.append('%03X=%r' % (g, mapping[g]))
    if row:
        print('  %s: %s' % (name, '  '.join(row)))

json.dump({'%04X' % g: c for g, c in sorted(mapping.items())},
          open("./_work_ar/"data\glyph_map.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('wrote data/glyph_map.json')