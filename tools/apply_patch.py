# -*- coding: utf-8 -*-
"""Splice rebuilt members into the ARC files and the disc, then emit a .bps patch."""
import json
import os
import struct
import zlib

SRC = r'./Megaman X4.bin'
WORK = r'./_work_ar'
OUT = os.path.join(WORK, 'out')
USER = 2048
ALIGN = 0x800

FILES = os.path.join(WORK, 'disc', 'files.txt')
ents = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        ents[p[0]] = (int(p[1]), int(p[2]))

data = bytearray(open(SRC, 'rb').read())
print('source bin:', len(data), 'bytes')


def arc_blob(arc_name):
    """Read an ARC file from the raw 2352-byte-sector disc image."""
    lba, size = ents[arc_name]
    out = bytearray()
    got = 0
    sec = lba
    while got < size:
        raw = data[sec * 2352:(sec + 1) * 2352]
        out += raw[24:24 + USER]
        got += USER
        sec += 1
    return bytes(out[:size])


def write_arc_blob(arc_name, blob):
    lba, size = ents[arc_name]
    assert len(blob) == size
    sec = lba
    done = 0
    while done < size:
        chunk = blob[done:done + USER]
        chunk += b'\x00' * (USER - len(chunk))
        base = sec * 2352
        data[base + 24:base + 24 + USER] = chunk
        done += USER
        sec += 1


def patch_arc(arc_name, member_index, new_member):
    blob = bytearray(arc_blob(arc_name))
    count, total = struct.unpack('<II', blob[:8])
    table = []
    for i in range(count):
        if i == 0:
            t, s = struct.unpack('<II', blob[8:16])
        else:
            t, s = struct.unpack('<II', blob[0x10 + (i - 1) * 8:0x18 + (i - 1) * 8])
        table.append((t, s))

    off = ALIGN
    for i, (t, s) in enumerate(table):
        if i == member_index:
            if len(new_member) > s:
                raise SystemExit('member %d too big: %d > %d' % (i, len(new_member), s))
            padded = new_member + b'\x00' * (s - len(new_member))
            blob[off:off + s] = padded
        off += s
        if s % ALIGN:
            off += ALIGN - (s % ALIGN)

    write_arc_blob(arc_name, bytes(blob))
    print('patched %-22s member[%d] type=0x%08X size=%d'
          % (arc_name, member_index, table[member_index][0], table[member_index][1]))


def find_member_index(arc_name, wanted_type):
    blob = arc_blob(arc_name)
    count, total = struct.unpack('<II', blob[:8])
    print('  %s: count=%d total=%d' % (arc_name, count, total))
    for i in range(count):
        off = 8 if i == 0 else 0x10 + (i - 1) * 8
        if off + 8 > len(blob):
            print('  !! table overruns at i=%d' % i)
            break
        t, s = struct.unpack('<II', blob[off:off + 8])
        if t == wanted_type:
            return i
    return -1


def patch_file(file_name, new_bytes):
    lba, size = ents[file_name]
    assert len(new_bytes) == size, f'Size mismatch for {file_name}: {len(new_bytes)} != {size}'
    sec = lba
    done = 0
    while done < size:
        chunk = new_bytes[done:done + USER]
        chunk += b'\x00' * (USER - len(chunk))
        base = sec * 2352
        data[base + 24:base + 24 + USER] = chunk
        done += USER
        sec += 1
    print('patched %-22s at LBA %d (%d bytes)' % (file_name, lba, size))


new_x = open(os.path.join(OUT, 'new_PL00_U_00000015.bin'), 'rb').read()
new_z = open(os.path.join(OUT, 'new_PL01_U_00000015.bin'), 'rb').read()

patch_arc('ARC/PL00_U.ARC', find_member_index('ARC/PL00_U.ARC', 0x00000015), new_x)
patch_arc('ARC/PL01_U.ARC', find_member_index('ARC/PL01_U.ARC', 0x00000015), new_z)

# the dialogue atlas must carry the new Arabic glyphs
atlas = open(os.path.join(WORK, 'arc', 'LOAD_U', '00010001.bin'), 'rb').read()
patch_arc('ARC/LOAD_U.ARC', find_member_index('ARC/LOAD_U.ARC', 0x00010001), atlas)

# patch SLUS_005.61 with native RTL dialogue rendering engine
if os.path.exists(os.path.join(OUT, 'SLUS_005.61')):
    patched_slus = open(os.path.join(OUT, 'SLUS_005.61'), 'rb').read()
    patch_file('SLUS_005.61', patched_slus)

patched = os.path.join(OUT, 'Megaman X4 (Arabic).bin')
open(patched, 'wb').write(bytes(data))
print('patched bin:', patched, os.path.getsize(patched), 'bytes')


# ------------------------------------------------------------------ BPS v1
from generate_bps import create_bps

create_bps(SRC, patched, os.path.join(OUT, 'MegaManX4_Arabic.bps'), verify=True)
