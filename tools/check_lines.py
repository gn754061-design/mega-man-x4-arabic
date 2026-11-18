# -*- coding: utf-8 -*-
import json

cat = json.load(open("./_work_ar/"out\ar_catalog.json', encoding='utf-8'))
print('Total entries:', len(cat['entries']))

max_line_len = 0
long_lines = []
over_3_lines = []

for e in cat['entries']:
    t = e.get('translation', '')
    if not t.strip(): continue
    pages = t.split('\f')
    for pi, page in enumerate(pages):
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        if len(lines) > 3:
            over_3_lines.append((e['id'], pi, len(lines)))
        for li, line in enumerate(lines):
            if len(line) > max_line_len:
                max_line_len = len(line)
            if len(line) > 20:
                long_lines.append((e['id'], pi, li, len(line), line))

print('Max line length in characters:', max_line_len)
print('Pages with > 3 lines:', len(over_3_lines))
print('Lines longer than 20 chars:', len(long_lines))
for ll in long_lines[:15]:
    print('  %-18s p%d l%d (%2d chars): %s' % (ll[0], ll[1], ll[2], ll[3], ll[4]))
