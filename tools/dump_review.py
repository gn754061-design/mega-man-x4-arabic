# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = r'./_work_ar'
cat = json.load(open(os.path.join(BASE_DIR, 'out', 'ar_catalog.json'), encoding='utf-8'))
out_path = os.path.join(BASE_DIR, 'out', 'dump_all_dialogue.txt')

with open(out_path, 'w', encoding='utf-8') as out:
    for i, e in enumerate(cat['entries']):
        eid = e['id']
        orig = e.get('original', '')
        trans = e.get('translation', '')
        out.write(f"=== [{i:03d}] {eid} ===\n")
        out.write("[ORIGINAL]\n" + orig + "\n")
        out.write("[CURRENT]\n" + trans + "\n\n")

print(f"Dumped {len(cat['entries'])} entries to {out_path}")
