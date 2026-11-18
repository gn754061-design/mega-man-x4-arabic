# -*- coding: utf-8 -*-
"""Mega Man X4 message codec.

Member layout (verified against PL00_U.ARC type 0x15):
    u16 count
    u16 offset[count]        byte offset of each message
    messages at those offsets, each a u16 stream:
        glyph = code & 0x7FF
        0x0800 = colour/flag (stage-name highlight)
        0x1000 = end-of-line   (last glyph of a line == '\\n')
        0x2000 = end of textbox  ('\\f')
        0x8000 = end of message

Uppercase glyph = 0x4A + (c - 'A')   -> 'A' = 0x4A
Lowercase glyph = 0x64 + (c - 'a')   -> 'a' = 0x64
Space           = 0x1FF
"""
import json
import os
import struct

ARC = "./_work_ar/"arc'
CAT = "./_work_ar/"data\source_text.json'

END = 0x8000
BOX = 0x2000
EOL = 0x1000
COL = 0x0800
MASK = 0x07FF

UPPER = {0x4A + i: chr(ord('A') + i) for i in range(26)}
LOWER = {0x64 + i: chr(ord('a') + i) for i in range(26)}
EXTRA = {0x1FF: ' '}


def build_table():
    t = {}
    t.update(EXTRA)
    t.update(UPPER)
    t.update(LOWER)
    return t


def decode(codes, table):
    out = []
    for c in codes:
        if c & END:
            break
        if c & BOX:
            out.append('\f')
            continue
        g = c & MASK
        if c & EOL:
            out.append(table.get(g, None))
            out.append('\n')
        else:
            out.append(table.get(g, None))
    # join, replacing unknown glyphs with a marker that keeps the slot visible
    s = ''
    for ch in out:
        if ch is None:
            s += '?'
        else:
            s += ch
    return s


def read_messages(path, table):
    data = open(path, 'rb').read()
    count = struct.unpack('<H', data[:2])[0]
    offs = struct.unpack('<%dH' % count, data[2:2 + count * 2])
    msgs = []
    for i, off in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(data)
        blob = data[off:end]
        n = len(blob) // 2
        codes = struct.unpack('<%dH' % n, blob[:n * 2])
        msgs.append((off, decode(codes, table), codes))
    return count, offs, msgs


if __name__ == '__main__':
    table = build_table()
    src = json.load(open(CAT, encoding='utf-8'))
    known = {e['id']: e['source'] for e in src['entries']}

    for label, rel, prefix in [('X', r'PL00_U\00000015.bin', 'dialogue.x.'),
                               ('Zero', r'PL01_U\00000015.bin', 'dialogue.zero.')]:
        p = os.path.join(ARC, rel)
        if not os.path.isfile(p):
            print('missing', p)
            continue
        count, offs, msgs = read_messages(p, table)
        print('=' * 72)
        print('%s campaign: %s  messages=%d' % (label, rel, count))
        ok = 0
        for i, (off, txt, codes) in enumerate(msgs):
            eid = '%s%03d' % (prefix, i)
            exp = known.get(eid)
            if exp is None:
                continue
            got = txt.rstrip('\n')
            want = exp.replace('\n', '\n')
            match = (got == want)
            ok += match
            if i < 3 or not match:
                print('  %s %s off=0x%04X' % (eid, 'MATCH' if match else 'DIFF ', off))
                if not match:
                    print('     want:', repr(want[:110]))
                    print('     got :', repr(got[:110]))
        print('  matched %d / %d' % (ok, len([1 for m in msgs])))