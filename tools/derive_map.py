# -*- coding: utf-8 -*-
"""Align known English plaintext against the code stream to derive the exact codec."""
import json
import os
import struct

ARC = "./_work_ar/"arc'
CAT = "./_work_ar/"data\source_text.json'

END, BOX, EOL, COL, MASK = 0x8000, 0x2000, 0x1000, 0x0800, 0x07FF


def load(path):
    data = open(path, 'rb').read()
    first = struct.unpack('<H', data[:2])[0]
    count = first // 2
    offs = list(struct.unpack('<%dH' % count, data[:2 + count * 2 - 2 + 2 - 2 + 2 - 2][:count]) ) if False else list(struct.unpack('<%dH' % count, data[0:count * 2]))
    msgs = []
    for i, off in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(data)
        blob = data[off:end]
        n = len(blob) // 2
        codes = struct.unpack('<%dH' % n, blob[:n * 2])
        msgs.append(codes)
    return count, offs, msgs


def strip_ctrl(codes):
    out = []
    for c in codes:
        if c & END:
            break
        if c & BOX:
            out.append('\\f')
            continue
        if c & EOL:
            out.append('\\n')
        out.append(c & MASK)
    return out


src = json.load(open(CAT, encoding='utf-8'))
known = {e['id']: e['source'] for e in src['entries']}

mapping = {}
conflicts = []
report = []

for label, rel, prefix in [('X', r'PL00_U\00000015.bin', 'dialogue.x.'),
                           ('Zero', r'PL01_U\00000015.bin', 'dialogue.zero.')]:
    p = os.path.join(ARC, rel)
    if not os.path.isfile(p):
        print('missing', p)
        continue
    count, offs, msgs = load(p)
    print('=' * 72)
    print('%s: %s  count=%d first_off=0x%X' % (label, rel, count, offs[0]))
    matched = 0
    for i, codes in enumerate(msgs):
        eid = '%s%03d' % (prefix, i)
        exp = known.get(eid)
        if exp is None:
            continue
        # expected char stream with \n,\f kept as markers
        want = exp.replace('\n', '\\n').replace('\f', '\\f')
        got = strip_ctrl(codes)
        # build char list from want
        wchars = []
        j = 0
        while j < len(want):
            if want[j] == '\\' and j + 1 < len(want) and want[j + 1] in 'nf':
                wchars.append(want[j:j + 2])
                j += 2
            else:
                wchars.append(want[j])
                j += 1
        # got is a flat list of ints and '\n'/'\\f' markers
        gchars = [('\\n' if x == '\\n' else ('\\f' if x == '\\f' else x)) for x in got]
        if len(gchars) == len(wchars):
            matched += 1
            for g, w in zip(gchars, wchars):
                if w in ('\\n', '\\f'):
                    continue
                if g in ('\\n', '\\f'):
                    conflicts.append((eid, 'marker-mismatch', g, w))
                    continue
                if g in mapping and mapping[g] != w:
                    conflicts.append((eid, g, mapping[g], w))
                else:
                    mapping[g] = w
        else:
            report.append((eid, len(wchars), len(gchars)))
    print('  aligned %d' % matched)

print()
print('glyph mappings derived:', len(mapping))
print('conflicts:', len(conflicts))
for c in conflicts[:10]:
    print('   ', c)
print()
print('length mismatches:', len(report))
for r in report[:8]:
    print('   ', r)
print()
items = sorted(mapping.items())
print('mapping (glyph -> char):')
print('  ' + '  '.join('%04X=%r' % (g, c) for g, c in items[:120]))