# -*- coding: utf-8 -*-
import os
import struct
import json
from PIL import Image

BASE_DIR = r'C:\Users\user\Desktop\m x4\_work_ar'
BIN_PATH = os.path.join(BASE_DIR, 'out', 'Megaman X4 (Arabic).bin')
FILES = os.path.join(BASE_DIR, 'disc', 'files.txt')
USER = 2048

ents = {}
for line in open(FILES, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) == 3:
        ents[p[0]] = (int(p[1]), int(p[2]))

f = open(BIN_PATH, 'rb')

def read_arc_member(arc_name, member_type):
    lba, size = ents[arc_name]
    f.seek(lba * 2352)
    # read sectors
    n_sec = (size + USER - 1) // USER
    raw_data = bytearray()
    for _ in range(n_sec):
        sec = f.read(2352)
        raw_data.extend(sec[24:24+USER])
    blob = raw_data[:size]
    
    count, total = struct.unpack('<II', blob[:8])
    off = 0x800
    for i in range(count):
        mid, msize = struct.unpack('<II', blob[8+i*8:16+i*8])
        if mid == member_type:
            return bytes(blob[off:off+msize])
        off = (off + msize + 0x7FF) // 0x800 * 0x800
    return None

# 1. Verify LOAD_U 0x00010001
atlas_data = read_arc_member('ARC/LOAD_U.ARC', 0x00010001)
print(f'Atlas member size: {len(atlas_data)} bytes')
local_atlas = open(os.path.join(BASE_DIR, 'arc', 'LOAD_U', '00010001.bin'), 'rb').read()
assert atlas_data == local_atlas, "Atlas mismatch!"
print('Atlas in patched BIN matches local LOAD_U/00010001.bin exactly!')

# 2. Verify PL00_U 0x00000015
x_data = read_arc_member('ARC/PL00_U.ARC', 0x00000015)
print(f'X member size: {len(x_data)} bytes')
local_x = open(os.path.join(BASE_DIR, 'arc', 'PL00_U', '00000015.bin'), 'rb').read()
assert x_data == local_x, "X dialogue mismatch!"
print('X dialogue in patched BIN matches local PL00_U/00000015.bin exactly!')

# 3. Verify PL01_U 0x00000015
z_data = read_arc_member('ARC/PL01_U.ARC', 0x00000015)
print(f'Zero member size: {len(z_data)} bytes')
local_z = open(os.path.join(BASE_DIR, 'arc', 'PL01_U', '00000015.bin'), 'rb').read()
assert z_data == local_z, "Zero dialogue mismatch!"
print('Zero dialogue in patched BIN matches local PL01_U/00000015.bin exactly!')

# 4. Verify SLUS_005.61 RTL opcodes
lba_slus, size_slus = ents['SLUS_005.61']
f.seek(lba_slus * 2352)
n_sec_slus = (size_slus + USER - 1) // USER
slus_bytes = bytearray()
for _ in range(n_sec_slus):
    sec = f.read(2352)
    slus_bytes.extend(sec[24:24+USER])
slus_disc = bytes(slus_bytes[:size_slus])
local_slus = open(os.path.join(BASE_DIR, 'out', 'SLUS_005.61'), 'rb').read()
assert slus_disc == local_slus, "SLUS mismatch!"
print('SLUS_005.61 in patched BIN matches local out/SLUS_005.61 exactly!')

# Verify exact RTL opcodes in disc image
assert slus_disc[0x012D74:0x012D78] == bytes([0x6C, 0x00, 0x02, 0x24]), "RTL opcode 1 mismatch!"
assert slus_disc[0x0137E8:0x0137EC] == bytes([0x6C, 0x00, 0x02, 0x24]), "RTL opcode 2 mismatch!"
assert slus_disc[0x013C64:0x013C68] == bytes([0x6C, 0x00, 0x02, 0x24]), "RTL opcode 3 mismatch!"
assert slus_disc[0x013C80:0x013C84] == bytes([0xF4, 0xFF, 0x42, 0x24]), "RTL opcode 4 mismatch!"
print('All 4 RTL engine opcodes verified in disc image!')

# 5. Decode first 3 messages from patched BIN to verify text
first_off = struct.unpack('<H', x_data[:2])[0]
n_msgs = first_off // 2
offsets = [struct.unpack('<H', x_data[i*2:i*2+2])[0] for i in range(n_msgs)]

print('\nDecoded Messages Verification:')
for mi in range(3):
    start = offsets[mi]
    end = offsets[mi+1] if mi+1 < n_msgs else len(x_data)
    u16s = [struct.unpack('<H', x_data[j:j+2])[0] for j in range(start, end, 2)]
    # Check flags
    has_line_break = any(bool(w & 0x4000) for w in u16s)
    has_page_break = any(bool(w & 0x2000) for w in u16s)
    has_end_msg = any(bool(w & 0x8000) for w in u16s)
    print(f'Msg {mi}: {len(u16s)} codes | LineBreak: {has_line_break} | PageBreak: {has_page_break} | EndMsg: {has_end_msg}')

print('\nALL CHECKS PASSED!')
