# -*- coding: utf-8 -*-
"""Search for menu strings encoded with the game's own codec (u16 glyph codes)."""
import os
import struct

WORK = r'C:\Users\user\Desktop\m x4\_work_ar'

# glyph codes from the verified codec
G = {'A': 0x4A, 'B': 0x4B, 'C': 0x4C, 'D': 0x4D, 'E': 0x4E, 'F': 0x4F,
     'G': 0x50, 'H': 0x51, 'I': 0x52, 'J': 0x53, 'K': 0x54, 'L': 0x55,
     'M': 0x56, 'N': 0x57, 'O': 0x58, 'P': 0x59, 'Q': 0x5A, 'R': 0x5B,
     'S': 0x5C, 'T': 0x5D, 'U': 0x5E, 'V': 0x5F, 'W': 0x60, 'X': 0x61,
     'Y': 0x62, 'Z': 0x63, ' ': 0x1FF}

WORDS = ['NEW GAME', 'CONTINUE', 'OPTION', 'SAVE', 'LOAD', 'EXIT', 'START',
         'SELECT', 'WEAPON', 'CHARACTER', 'VERSUS', 'TRAINING', 'NAME',
         'PASSWORD', 'DELETE', 'YES', 'NO', 'MODE', 'DIFFICULTY', 'TIME']

patterns = {}
for w in WORDS:
    if all(ch in G for ch in w):
        pat = b''.join(struct.pack('<H', G[ch]) for ch in w)
        patterns[w] = pat
    # also without the 0x0800 flag variants (plain codes)
    pat2 = b''.join(struct.pack('<H', G[ch] & 0x7FF) for ch in w)
    patterns[w + ' (no flags)'] = pat2

roots = [os.path.join(WORK, 'arc'), os.path.join(WORK, 'disc', 'extracted')]
files = []
for r in roots:
    for dp, _, fs in os.walk(r):
        for f in fs:
            if f.endswith('.bin') or f == 'SLUS_005.61':
                files.append(os.path.join(dp, f))

print('files scanned:', len(files))
total_hits = 0
for w, pat in patterns.items():
    hits = []
    for p in files:
        try:
            data = open(p, 'rb').read()
        except Exception:
            continue
        i = data.find(pat)
        if i >= 0:
            hits.append((i, p))
    if hits:
        total_hits += len(hits)
        print('\n%-20s : %d hit(s)' % (w, len(hits)))
        for off, p in hits[:4]:
            print('    0x%06X %s' % (off, os.path.relpath(p, WORK)))
            data = open(p, 'rb').read()
            ctx = data[max(0, off - 32):off + len(pat) + 48]
            codes = struct.unpack('<%dH' % (len(ctx) // 2), ctx[:len(ctx) // 2 * 2])
            print('       ', ' '.join('%03X' % (c & 0x7FF) for c in codes))

print()
print('total hits:', total_hits)