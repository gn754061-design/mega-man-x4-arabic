# -*- coding: utf-8 -*-
"""Extract an ISO9660 filesystem from a MODE2/2352 PS1 .bin.

Writes a flat 2048-bytes-per-sector image plus an LBA map, then parses the
ISO9660 PVD and root directory to list every file with its LBA and size.
"""
import os
import struct
import sys

SECTOR = 2352
USER = 2048


def extract(bin_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    raw_path = bin_path
    flat_path = os.path.join(out_dir, 'disc.iso')
    lba_map_path = os.path.join(out_dir, 'lba_map.txt')

    total = os.path.getsize(raw_path)
    n_sectors = total // SECTOR
    print('bin bytes   :', total)
    print('sector size :', SECTOR)
    print('sectors     :', n_sectors)

    lba = 0
    lba_map = []
    with open(raw_path, 'rb') as fin, open(flat_path, 'wb') as fout:
        for i in range(n_sectors):
            fin.seek(i * SECTOR)
            sec = fin.read(SECTOR)
            if len(sec) < SECTOR:
                break
            mode = sec[15]
            if mode == 2:
                submode = sec[18]
                if submode & 0x20:
                    # Mode 2 Form 2 (XA audio/video) — 2324 bytes, no filesystem payload
                    fout.write(b'\x00' * USER)
                    lba_map.append((lba, i, 'form2-xa'))
                    lba += 1
                    continue
                data = sec[24:24 + USER]
                fout.write(data)
                lba_map.append((lba, i, 'form1-data'))
                lba += 1
            elif mode == 1:
                fout.write(sec[16:16 + USER])
                lba_map.append((lba, i, 'mode1-data'))
                lba += 1
            else:
                fout.write(b'\x00' * USER)
                lba_map.append((lba, i, 'raw-%d' % mode))
                lba += 1

    with open(lba_map_path, 'w', encoding='utf-8', newline='\n') as f:
        for l, s, kind in lba_map:
            f.write('%d\t%d\t%s\n' % (l, s, kind))

    print('user sectors:', lba)
    print('flat image  :', flat_path, os.path.getsize(flat_path), 'bytes')
    return flat_path


def read_sector(flat, lba):
    flat.seek(lba * USER)
    return flat.read(USER)


def parse_iso(flat_path):
    with open(flat_path, 'rb') as flat:
        pvd = None
        for lba in range(16, 24):
            sec = read_sector(flat, lba)
            if len(sec) < USER:
                break
            if sec[0] == 1 and sec[1:6] == b'CD001':
                pvd = sec
                break
        if pvd is None:
            print('no PVD found')
            return

        vol_id = pvd[40:72].decode('ascii', 'replace').strip()
        vol_size = struct.unpack('<I', pvd[80:84])[0]
        root_rec = pvd[156:156 + 34]
        root_lba = struct.unpack('<I', root_rec[2:6])[0]
        root_len = struct.unpack('<I', root_rec[10:14])[0]
        print('volume id   :', vol_id)
        print('volume size :', vol_size, 'blocks')
        print('root dir    : lba %d len %d' % (root_lba, root_len))

        files = []

        def walk(lba, length, prefix, depth):
            if depth > 8:
                return
            data = b''
            need = length
            cur = lba
            while need > 0:
                sec = read_sector(flat, cur)
                take = min(USER, need)
                data += sec[:take]
                need -= take
                cur += 1
            pos = 0
            while pos < len(data):
                rlen = data[pos]
                if rlen == 0:
                    pos = (pos // USER + 1) * USER
                    continue
                rec = data[pos:pos + rlen]
                if len(rec) < 33:
                    break
                ext = struct.unpack('<I', rec[2:6])[0]
                size = struct.unpack('<I', rec[10:14])[0]
                flags = rec[25]
                nlen = rec[32]
                name = rec[33:33 + nlen]
                pos += rlen
                try:
                    nm = name.decode('ascii')
                except Exception:
                    continue
                if nm in ('\x00', '\x01'):
                    continue
                nm = nm.split(';')[0]
                full = prefix + nm
                if flags & 2:
                    walk(ext, size, full + '/', depth + 1)
                else:
                    files.append((full, ext, size))

        walk(root_lba, root_len, '', 0)
        print('files       :', len(files))
        return files


if __name__ == '__main__':
    binp = sys.argv[1] if len(sys.argv) > 1 else "./"m x4\New folder\Megaman X4.bin'
    outd = sys.argv[2] if len(sys.argv) > 2 else "./_work_ar/"disc'
    flat = extract(binp, outd)
    files = parse_iso(flat)
    if files:
        with open(os.path.join(outd, 'files.txt'), 'w', encoding='utf-8', newline='\n') as f:
            for name, lba, size in files:
                f.write('%s\t%d\t%d\n' % (name, lba, size))
        for name, lba, size in files[:80]:
            print('  %-42s lba %8d  %10d' % (name, lba, size))