# -*- coding: utf-8 -*-
"""Produce a pre-shaped, visually ordered form of the Arabic catalog.

Use this only if a renderer needs presentation forms (Arabic Presentation Forms-B)
or a pre-reversed run. Control codes are never touched.

Usage:
    python scripts/reshape_ar.py <catalog.json> <output.json> [--no-bidi]

Without --no-bidi the output uses arabic_reshaper + python-bidi (visual order).
With --no-bidi it emits presentation forms while keeping logical order.
"""
import json
import re
import sys

import arabic_reshaper
from bidi.algorithm import get_display

TAG = re.compile(r'(\f|\n)')


def reshape_segment(seg):
    return get_display(arabic_reshaper.reshape(seg))


def reshape_text(text, do_bidi=True):
    out = []
    for part in TAG.split(text):
        if part in ('\f', '\n'):
            out.append(part)
        elif part:
            reshaped = arabic_reshaper.reshape(part)
            out.append(get_display(reshaped) if do_bidi else reshaped)
    return ''.join(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, dst = sys.argv[1], sys.argv[2]
    do_bidi = '--no-bidi' not in sys.argv

    cat = json.load(open(src, encoding='utf-8'))
    for e in cat['entries']:
        e['translation'] = reshape_text(e['translation'], do_bidi)

    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print('rewrote %d entries -> %s (bidi=%s)' % (len(cat['entries']), dst, do_bidi))
    print('sample:', repr(cat['entries'][0]['translation'][:80]))
    return 0


if __name__ == '__main__':
    sys.exit(main())