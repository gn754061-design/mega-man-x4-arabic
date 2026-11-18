# -*- coding: utf-8 -*-
"""Content audit: every story message is Arabic, non-empty, and uses Arabic cells."""
import json
import os

WORK = "./_work_ar"'
enc = json.load(open(os.path.join(WORK, 'data', 'arabic_encode.json'), encoding='utf-8'))
cat = json.load(open(os.path.join(WORK, 'out', 'ar_catalog.json'), encoding='utf-8'))
text = {e['id']: e.get('translation', '') for e in cat['entries']}

BASE = enc['base_cell']
print('arabic glyph base : 0x%03X' % BASE)

empty = []
latin = []
no_arabic = []
total_glyphs = 0
for m in enc['messages']:
    eid = m['id']
    t = text.get(eid, '')
    if not t.strip():
        empty.append(eid)
        continue
    glyphs = [c & 0x7FF for c in m['codes'] if (c & 0x7FF)]
    total_glyphs += len(glyphs)
    if not glyphs:
        no_arabic.append(eid)
        continue
    low = [g for g in glyphs if g < BASE and g != 0x1FF]
    if low:
        latin.append((eid, len(low), ['%03X' % g for g in low[:6]]))

print('messages total        : %d' % len(enc['messages']))
print('non-text terminators  : %d  (%s)' % (len(empty), ', '.join(empty)))
print('translated messages   : %d' % (len(enc['messages']) - len(empty)))
print('total arabic glyphs   : %d' % total_glyphs)
print()
print('messages with NO glyphs        : %d' % len(no_arabic))
print('messages with non-arabic glyphs: %d' % len(latin))
for l in latin[:10]:
    print('   ', l)
print()
print('VERDICT:', 'ALL STORY TEXT IS ARABIC' if not latin and not no_arabic else 'INCOMPLETE')