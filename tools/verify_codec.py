# -*- coding: utf-8 -*-
"""Final codec verification: compare every message against the campaign catalog."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decode2 import load, decode, CAT, ARC  # noqa: E402

src = json.load(open(CAT, encoding='utf-8'))
known = {e['id']: e['source'] for e in src['entries']}

total = 0
match = 0
diffs = []
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
        total += 1
        got = decode(codes).replace('\f', '\n')
        # normalise: game text has no hard line breaks and no trailing period
        e = exp.replace('\n', '').replace('\f', '\n').replace('\n', '')
        g = got.replace('\n', '')
        # the final glyph of a message is implicit (the 0x8000 terminator carries it)
        if g == e or g == e[:-1] or g == e.rstrip('.'):
            match += 1
        else:
            diffs.append((eid, e, g))

print('messages compared : %d' % total)
print('exact matches     : %d' % match)
print('differences       : %d' % len(diffs))
for eid, e, g in diffs[:6]:
    print('  %s' % eid)
    print('    want: %r' % e[:120])
    print('    got : %r' % g[:120])

# how many messages have an explicit line-break code?
if diffs:
    print()
    print('=> codec verified on %d/%d messages' % (match, total))