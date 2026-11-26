# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = r'./_work_ar'
cat = json.load(open(os.path.join(BASE_DIR, 'out', 'ar_catalog.json'), encoding='utf-8'))

print(f"Total entries: {len(cat['entries'])}")
orphan_count = 0

for i, e in enumerate(cat['entries']):
    eid = e['id']
    orig = e.get('original', '')
    trans = e.get('translation', '')
    if trans == '{glyph:38}':
        continue
    pages = trans.split('\f')
    orig_pages = orig.split('\f')
    
    underfilled = []
    for pi, page in enumerate(pages):
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        body = lines[1:] if len(lines) > 1 else lines
        if len(body) == 1:
            underfilled.append((pi, body[0]))
        else:
            for bl in body:
                if len(bl.split()) <= 1:
                    underfilled.append((pi, bl))
                    
    if underfilled:
        orphan_count += 1
        print(f"[{i:03d}] {eid} ({len(pages)} pages vs orig {len(orig_pages)}):")
        for pi, txt in underfilled:
            print(f"    p{pi}: '{txt}'")

print(f"\nTotal entries with orphan/single-line pages: {orphan_count}")
