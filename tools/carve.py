# -*- coding: utf-8 -*-
"""Carve named files out of the flat ISO and dump their structure."""
import os
import struct

ISO = r'./_work_ar\disc\disc.iso'
OUT = r'./_work_ar\disc\extracted'
FILES = r'./_work_ar\disc\files.txt'
USER = 2048

os.makedirs(OUT, exist_ok=True)

entries = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        entries[p[0]] = (int(p[1]), int(p[2]))

iso = open(ISO, 'rb')

for name in ['ARC/LOAD_U.ARC', 'ARC/FONT8X8.ARC', 'ARC/MOJIPAT.ARC',
             'ARC/CAPCOM.ARC', 'SLUS_005.61', 'SYSTEM.CNF']:
    if name not in entries:
        print('missing', name)
        continue
    lba, size = entries[name]
    iso.seek(lba * USER)
    blob = iso.read(size)
    out = os.path.join(OUT, name.replace('/', '_'))
    open(out, 'wb').write(blob)
    print('%-18s lba %7d size %8d -> %s' % (name, lba, size, out))
    head = blob[:64]
    print('    head:', head.hex(' '))
    print('    ascii:', repr(head[:40]))

print()
print('=== LOAD_U.ARC first 256 bytes as u32 LE ===')
blob = open(os.path.join(OUT, 'ARC_LOAD_U.ARC'), 'rb').read(512)
for i in range(0, 256, 16):
    vals = struct.unpack('<4I', blob[i:i + 16])
    print('  +0x%03X: %s' % (i, ' '.join('%08X' % v for v in vals)))

print()
print('=== FONT8X8.ARC first 128 bytes ===')
blob = open(os.path.join(OUT, 'ARC_FONT8X8.ARC'), 'rb').read(128)
print('  hex:', blob.hex(' '))
print('  u32:', ' '.join('%08X' % v for v in struct.unpack('<32I', blob)))