# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = r'C:\Users\user\Desktop\m x4\_work_ar'
cat = json.load(open(os.path.join(BASE_DIR, 'out', 'ar_catalog.json'), encoding='utf-8'))

for mi in [0, 8, 11, 25, 30, 31]:
    e = cat['entries'][mi]
    orig_pages = e['original'].split('\f')
    print(f"=== Entry {mi} {e['id']} ({len(orig_pages)} pages) ===")
    for pi, p in enumerate(orig_pages):
        print(f"  [p{pi}] " + " // ".join(p.split('\n')))
