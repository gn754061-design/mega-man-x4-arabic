#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spec-compliant BPS1 delta patch generator + built-in round-trip apply verifier
for Mega Man X4 (PS1, SLUS-00561).

Uses SourceRead (action 0) for unchanged regions and TargetRead (action 1) only
for changed regions, producing a tiny legal delta patch (~40-50 KB for a 592 MB disc).
"""
import argparse
import hashlib
import os
import struct
import zlib


def encode_varint(n: int) -> bytes:
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            break
        out.append(x)
        n -= 1
    return bytes(out)


def decode_varint(data: bytes, pos: int):
    val = 0
    shift = 1
    while True:
        b = data[pos]
        pos += 1
        val += (b & 0x7F) * shift
        if b & 0x80:
            return val, pos
        shift <<= 7
        val += shift


def apply_bps(source: bytes, patch: bytes) -> bytearray:
    """Apply a BPS1 patch in memory to verify 100% byte-for-byte accuracy."""
    assert patch[:4] == b"BPS1", "Bad BPS1 magic"
    pos = 4
    src_len, pos = decode_varint(patch, pos)
    tgt_len, pos = decode_varint(patch, pos)
    meta_len, pos = decode_varint(patch, pos)
    pos += meta_len
    assert src_len == len(source), f"Source length mismatch: {src_len} != {len(source)}"
    end_cmds = len(patch) - 12
    target = bytearray()
    src_rel = 0
    tgt_rel = 0
    while pos < end_cmds:
        data, pos = decode_varint(patch, pos)
        action = data & 3
        length = (data >> 2) + 1
        if action == 0:  # SourceRead
            off = len(target)
            target.extend(source[off : off + length])
        elif action == 1:  # TargetRead
            target.extend(patch[pos : pos + length])
            pos += length
        elif action == 2:  # SourceCopy
            d, pos = decode_varint(patch, pos)
            src_rel += (-1 if (d & 1) else 1) * (d >> 1)
            target.extend(source[src_rel : src_rel + length])
            src_rel += length
        else:  # TargetCopy
            d, pos = decode_varint(patch, pos)
            tgt_rel += (-1 if (d & 1) else 1) * (d >> 1)
            for _ in range(length):
                target.append(target[tgt_rel])
                tgt_rel += 1
    assert len(target) == tgt_len, f"Target length mismatch: {len(target)} != {tgt_len}"
    src_crc, tgt_crc, patch_crc = struct.unpack("<III", patch[-12:])
    assert src_crc == (zlib.crc32(source) & 0xFFFFFFFF), "Source CRC32 mismatch"
    assert tgt_crc == (zlib.crc32(target) & 0xFFFFFFFF), "Target CRC32 mismatch"
    assert patch_crc == (zlib.crc32(patch[:-4]) & 0xFFFFFFFF), "Patch CRC32 mismatch"
    return target


def find_diff_regions_fast(source: bytes, target: bytes, min_gap: int = 32, chunk_size: int = 65536):
    """Fast chunked scan for differing byte ranges between two equal-length buffers."""
    n = min(len(source), len(target))
    raw_runs = []
    for off in range(0, n, chunk_size):
        end_off = min(off + chunk_size, n)
        if source[off:end_off] == target[off:end_off]:
            continue
        s1 = source[off:end_off]
        s2 = target[off:end_off]
        in_diff = False
        start = 0
        for i in range(len(s1)):
            if s1[i] != s2[i]:
                if not in_diff:
                    start = off + i
                    in_diff = True
            else:
                if in_diff:
                    raw_runs.append((start, off + i))
                    in_diff = False
        if in_diff:
            raw_runs.append((start, end_off))

    # Merge nearby diff runs when the unchanged gap is smaller than min_gap
    merged = []
    for s, e in raw_runs:
        if merged and s - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def create_bps(source_path: str, target_path: str, output_path: str, verify: bool = True) -> bytes:
    with open(source_path, "rb") as f:
        source = f.read()
    with open(target_path, "rb") as f:
        target = f.read()

    if len(source) != len(target):
        raise ValueError(f"Expected equal lengths, got {len(source)} vs {len(target)}")

    regions = find_diff_regions_fast(source, target, min_gap=32)

    patch = bytearray(b"BPS1")
    patch.extend(encode_varint(len(source)))
    patch.extend(encode_varint(len(target)))
    patch.extend(encode_varint(0))  # metadata length = 0

    pos = 0
    for rs, re_ in regions:
        if rs > pos:
            length = rs - pos
            patch.extend(encode_varint(((length - 1) << 2) | 0))  # SourceRead
        if re_ > rs:
            length = re_ - rs
            patch.extend(encode_varint(((length - 1) << 2) | 1))  # TargetRead
            patch.extend(target[rs:re_])
        pos = re_
    if pos < len(target):
        length = len(target) - pos
        patch.extend(encode_varint(((length - 1) << 2) | 0))  # SourceRead

    src_crc = zlib.crc32(source) & 0xFFFFFFFF
    tgt_crc = zlib.crc32(target) & 0xFFFFFFFF
    patch.extend(struct.pack("<I", src_crc))
    patch.extend(struct.pack("<I", tgt_crc))
    patch_crc = zlib.crc32(patch) & 0xFFFFFFFF
    patch.extend(struct.pack("<I", patch_crc))

    patch_bytes = bytes(patch)

    if verify:
        rebuilt = apply_bps(source, patch_bytes)
        assert rebuilt == target, "BPS1 round-trip verification FAILED!"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(patch_bytes)

    print(f"BPS1 patch written : {output_path}")
    print(f"Patch size         : {len(patch_bytes):,} bytes ({len(regions)} diff regions)")
    print(f"Source CRC32       : {src_crc:08X}")
    print(f"Source SHA-1       : {hashlib.sha1(source).hexdigest().upper()}")
    print(f"Source SHA-256     : {hashlib.sha256(source).hexdigest().upper()}")
    print(f"Target CRC32       : {tgt_crc:08X}")
    print(f"Target SHA-1       : {hashlib.sha1(target).hexdigest().upper()}")
    print(f"Target SHA-256     : {hashlib.sha256(target).hexdigest().upper()}")
    print(f"Patch  CRC32       : {patch_crc:08X}")
    if verify:
        print("Round-trip verify  : PASSED (100% byte-for-byte identical)")
    return patch_bytes


def main():
    parser = argparse.ArgumentParser(description="Create and verify a spec-compliant BPS1 patch for Mega Man X4 (PS1).")
    parser.add_argument("--source", default="./Megaman X4.bin", help="Clean original USA SLUS-00561 BIN")
    parser.add_argument("--target", default="./_work_ar/out/Megaman X4 (Arabic).bin", help="Arabic patched BIN")
    parser.add_argument("--output", default="./patches/MegaManX4_Arabic.bps", help="Output BPS1 patch path")
    parser.add_argument("--no-verify", action="store_true", help="Skip round-trip verification")
    args = parser.parse_args()
    create_bps(args.source, args.target, args.output, verify=not args.no_verify)


if __name__ == "__main__":
    main()
