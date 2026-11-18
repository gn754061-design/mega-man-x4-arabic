# -*- coding: utf-8 -*-
"""Full MMX4 message codec with verification against the campaign catalog."""
import json
import os
import struct
import sys

ARC = "./_work_ar/"arc'
CAT = "./_work_ar/"data\source_text.json'

END, BOX, EOL, COL, MASK = 0x8000, 0x2000, 0x1000, 0x0800, 0x07FF

TABLE = {}
for i in range(10):
    TABLE[0x40 + i] = str(i)
for i in range(26):
    TABLE[0x4A + i] = chr(ord('A') + i)
    TABLE[0x64 + i] = chr(ord('a') + i)
TABLE[0x1FF] = ' '
PUNCT = {0x83: '+', 0x84: '-', 0x85: ',', 0x86: '.', 0x87: '!', 0x88: '?', 0x8B: "'"}
TABLE.update(PUNCT)
TABLE[0x5F] = 'V'


def load(path):
    data = open(path, 'rb').read()
    count = struct.unpack('<H', data[:2])[0] // 2
    offs = list(struct.unpack('<%dH' % count, data[:count * 2]))
    msgs = []
    for i, off in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(data)
        blob = data[off:end]
        n = len(blob) // 2
        msgs.append(struct.unpack('<%dH' % n, blob[:n * 2]))
    return count, offs, msgs


def decode(codes):
    out = []
    for c in codes:
        if c & END:
            break
        g = c & MASK
        if g:
            out.append(TABLE.get(g, '\u2588'))
        if c & BOX:
            out.append('\f')
        if c & END:
            break
    return ''.join(out)


def main():
    src = json.load(open(CAT, encoding='utf-8'))
    known = {e['id']: e['source'] for e in src['entries']}
    for label, rel, prefix in [('X', r'PL00_U\00000015.bin', 'dialogue.x.'),
                               ('Zero', r'PL01_U\00000015.bin', 'dialogue.zero.')]:
        p = os.path.join(ARC, rel)
        if not os.path.isfile(p):
            continue
        count, offs, msgs = load(p)
        print('=' * 74)
        print('%s: %d messages' % (label, count))
        exact = 0
        nows = 0
        for i, codes in enumerate(msgs):
            eid = '%s%03d' % (prefix, i)
            exp = known.get(eid)
            if exp is None:
                continue
            got = decode(codes)
            e_flat = exp.replace('\n', '').replace('\f', '')
            g_flat = got.replace('\f', '')
            if g_flat == e_flat:
                exact += 1
            elif got.replace('\f', '\n') == exp:
                nows += 1
            if i < 4:
                print('  %s' % eid)
                print('    want:', repr(exp[:100]))
                print('    got :', repr(got[:100]))
        print('  exact flat match: %d   match-with-pagebreaks-as-newlines: %d' % (exact, nows))
        print()


if __name__ == '__main__':
    main()