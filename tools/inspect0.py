# -*- coding: utf-8 -*-
"""Print message 0 of each campaign with codes beside the known plaintext."""
import json
import os
import struct

ARC = "./_work_ar/"arc'
CAT = "./_work_ar/"data\source_text.json'
END, BOX, EOL, COL, MASK = 0x8000, 0x2000, 0x1000, 0x0800, 0x07FF

src = json.load(open(CAT, encoding='utf-8'))
known = {e['id']: e['source'] for e in src['entries']}


def load(path):
    data = open(path, 'rb').read()
    count = struct.unpack('<H', data[:2])[0] // 2
    offs = list(struct.unpack('<%dH' % count, data[:count * 2]))
    out = []
    for i, off in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(data)
        blob = data[off:end]
        n = len(blob) // 2
        out.append(struct.unpack('<%dH' % n, blob[:n * 2]))
    return count, offs, out


for label, rel, prefix, idx in [('X', r'PL00_U\00000015.bin', 'dialogue.x.', 1),
                                ('X', r'PL00_U\00000015.bin', 'dialogue.x.', 0),
                                ('Zero', r'PL01_U\00000015.bin', 'dialogue.zero.', 0)]:
    p = os.path.join(ARC, rel)
    count, offs, msgs = load(p)
    codes = msgs[idx]
    exp = known['%s%03d' % (prefix, idx)]
    print('=' * 74)
    print('%s %s%03d  codes=%d  chars_nospace=%d'
          % (label, prefix, idx, len(codes), len(exp)))
    print('expected:', repr(exp))
    seq = []
    for c in codes:
        if c & END:
            seq.append('<END>')
            break
        if c & BOX:
            seq.append('<BOX>')
            continue
        tag = ('L' if c & EOL else '.') + ('C' if c & COL else '.')
        seq.append('%s%03X' % (tag, c & MASK))
    print('codes   :', ' '.join(seq))
    print()