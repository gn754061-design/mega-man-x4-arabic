# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = r'./_work_ar'
cat = json.load(open(os.path.join(BASE_DIR, 'out', 'ar_catalog.json'), encoding='utf-8'))

out_file = os.path.join(BASE_DIR, 'out', 'all_english_entries.txt')
with open(out_file, 'w', encoding='utf-8') as f:
    for i, e in enumerate(cat['entries']):
        eid = e['id']
        orig = e.get('original', '')
        f.write(f"=== [{i:03d}] {eid} ===\n")
        pages = orig.split('\f')
        for pi, p in enumerate(pages):
            f.write(f"  [p{pi}] {repr(p)}\n")
        f.write("\n")

print(f"Dumped all {len(cat['entries'])} entries to {out_file}")
