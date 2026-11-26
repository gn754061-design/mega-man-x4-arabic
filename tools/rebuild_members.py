# -*- coding: utf-8 -*-
"""Check encoded Arabic fits the original ARC members, then rewrite them in place."""
import json
import os
import struct

ARC = r'./_work_ar\arc'
WORK = r'./_work_ar'

enc = json.load(open(os.path.join(WORK, 'data', 'arabic_encode.json'), encoding='utf-8'))
msgs = {m['id']: m['codes'] for m in enc['messages']}


def rebuild(path, prefix, out_path):
    data = open(path, 'rb').read()
    count = struct.unpack('<H', data[:2])[0] // 2
    offs = list(struct.unpack('<%dH' % count, data[:count * 2]))
    old_total = len(data)

    # build new message blobs
    blobs = []
    for i in range(count):
        eid = '%s%03d' % (prefix, i)
        codes = msgs.get(eid, [])
        # preserve the terminator; append 0x8000 when the encoder did not
        body = list(codes)
        if not body or not (body[-1] & 0x8000):
            body.append(0x8000)
        blobs.append(b''.join(struct.pack('<H', c) for c in body))

    table_len = count * 2
    off = table_len
    new_offs = []
    parts = []
    for b in blobs:
        new_offs.append(off)
        parts.append(b)
        off += len(b)

    total = off
    out = bytearray(total)
    struct.pack_into('<%dH' % count, out, 0, *new_offs)
    p = table_len
    for b in parts:
        out[p:p + len(b)] = b
        p += len(b)

    print('%s' % os.path.basename(path))
    print('   messages      : %d' % count)
    print('   original bytes: %d' % old_total)
    print('   new bytes     : %d' % total)
    print('   delta         : %+d' % (total - old_total))
    if total <= old_total:
        open(out_path, 'wb').write(bytes(out))
        print('   -> written %s' % out_path)
        return True
    print('   !! OVERFLOW by %d bytes' % (total - old_total))
    return False


ok1 = rebuild(os.path.join(ARC, 'PL00_U', '00000015.bin'), 'dialogue.x.',
              os.path.join(WORK, 'out', 'new_PL00_U_00000015.bin'))
print()
ok2 = rebuild(os.path.join(ARC, 'PL01_U', '00000015.bin'), 'dialogue.zero.',
              os.path.join(WORK, 'out', 'new_PL01_U_00000015.bin'))
print()
print('both fit:', ok1 and ok2)