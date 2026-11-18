# -*- coding: utf-8 -*-
"""Check that page breaks survive encoding: count 0x2000 codes vs '\\f' in the Arabic text."""
import json
import os

WORK = "./_work_ar"'
enc = json.load(open(os.path.join(WORK, 'data', 'arabic_encode.json'), encoding='utf-8'))
cat = json.load(open(os.path.join(WORK, 'out', 'ar_catalog.json'), encoding='utf-8'))
text = {e['id']: e.get('translation', '') for e in cat['entries']}

bad = []
for m in enc['messages']:
    eid = m['id']
    t = text.get(eid, '')
    want = t.count('\f')
    got = sum(1 for c in m['codes'] if (c & 0x2000))
    if want != got:
        bad.append((eid, want, got))

print('messages          : %d' % len(enc['messages']))
print('page-break match  : %d' % (len(enc['messages']) - len(bad)))
print('mismatches        : %d' % len(bad))
for b in bad[:10]:
    print('   ', b)

tot_boxes = sum(1 for m in enc['messages'] for c in m['codes'] if c & 0x2000)
tot_codes = sum(len(m['codes']) for m in enc['messages'])
print()
print('total codes       : %d' % tot_codes)
print('total page breaks : %d' % tot_boxes)
print('avg codes/message : %.1f' % (tot_codes / max(1, len(enc['messages']))))