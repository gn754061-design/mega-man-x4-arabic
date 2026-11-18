# -*- coding: utf-8 -*-
"""Search the EXE and small ARCs for 8-bit ASCII menu strings."""
import os
import re

WORK = "./_work_ar"'
TARGETS = [
    ('EXE', os.path.join(WORK, 'disc', 'extracted', 'SLUS_005.61')),
    ('LOAD_U/0x10008', os.path.join(WORK, 'arc', 'LOAD_U', '00010008.bin')),
    ('PL00_U/0x00000014', os.path.join(WORK, 'arc', 'PL00_U', '00000014.bin')),
    ('PL00_U/0x00000003', os.path.join(WORK, 'arc', 'PL00_U', '00000003.bin')),
    ('PL00_U/0x00000006', os.path.join(WORK, 'arc', 'PL00_U', '00000006.bin')),
    ('PL00_U/0x00000010', os.path.join(WORK, 'arc', 'PL00_U', '00000010.bin')),
    ('PL00_U/0x00000012', os.path.join(WORK, 'arc', 'PL00_U', '00000012.bin')),
]

WORDS = [b'NEW GAME', b'CONTINUE', b'OPTION', b'SAVE', b'LOAD', b'EXIT',
         b'START', b'SELECT', b'YES', b'NO', b'WEAPON', b'CHARACTER',
         b'VERSUS', b'TRAINING', b'ARCADE', b'NAME', b'PASSWORD', b'DELETE']

for label, p in TARGETS:
    if not os.path.isfile(p):
        print('%-20s MISSING' % label)
        continue
    data = open(p, 'rb').read()
    hits = []
    for w in WORDS:
        for m in re.finditer(re.escape(w), data, re.I):
            hits.append((m.start(), w.decode()))
    print('%-20s size=%8d  hits=%d' % (label, len(data), len(hits)))
    for off, w in hits[:8]:
        ctx = data[max(0, off - 16):off + len(w) + 24]
        print('     0x%06X %-9s %r' % (off, w, ctx))
    print()