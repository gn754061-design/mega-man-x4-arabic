# -*- coding: utf-8 -*-
"""Verify the patched disc: read the Arabic member back and decode it."""
import os
import struct
import sys

WORK = "./_work_ar"'
OUT = os.path.join(WORK, 'out')
USER = 2048
MASK, COL, EOL, BOX, END = 0x07FF, 0x0800, 0x1000, 0x2000, 0x8000

ents = {}
for line in open(os.path.join(WORK, 'disc', 'files.txt'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        ents[p[0]] = (int(p[1]), int(p[2]))

data = open(os.path.join(OUT, 'Megaman X4 (Arabic).bin'), 'rb').read()


def arc_blob(name):
    lba, size = ents[name]
    out = bytearray()
    got, sec = 0, lba
    while got < size:
        out += data[sec * 2352 + 24: sec * 2352 + 24 + USER]
        got += USER
        sec += 1
    return bytes(out[:size])


def member(blob, idx):
    count = struct.unpack('<I', blob[:4])[0]
    off = 0x800
    for i in range(count):
        if i == 0:
            t, s = struct.unpack('<II', blob[8:16])
        else:
            t, s = struct.unpack('<II', blob[0x10 + (i - 1) * 8:0x18 + (i - 1) * 8])
        if i == idx:
            return t, blob[off:off + s]
        off += s
        if s % 0x800:
            off += 0x800 - (s % 0x800)
    return None, None


for name, label in [('ARC/PL00_U.ARC', 'X'), ('ARC/PL01_U.ARC', 'Zero')]:
    blob = arc_blob(name)
    t, m = member(blob, 15)
    print('%s: type=0x%08X member bytes=%d' % (label, t, len(m)))
    count = struct.unpack('<H', m[:2])[0] // 2
    offs = list(struct.unpack('<%dH' % count, m[:count * 2]))
    print('   messages=%d first_off=0x%X' % (count, offs[0]))
    for i in (0, 1, 2):
        s = offs[i]
        e = offs[i + 1] if i + 1 < count else len(m)
        codes = struct.unpack('<%dH' % ((e - s) // 2), m[s:e])
        txt = []
        for c in codes:
            g = c & MASK
            if c & END:
                if g:
                    txt.append('U+%04X' % g)
                break
            if g:
                txt.append('U+%04X' % g)
            if c & BOX:
                txt.append('<BOX>')
        print('   msg%d (%d codes): %s' % (i, len(codes), ' '.join(txt[:14])))