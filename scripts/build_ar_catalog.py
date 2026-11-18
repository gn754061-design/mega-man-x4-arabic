# -*- coding: utf-8 -*-
"""Build the Arabic catalog and a community mod package from the validated batches."""
import json
import os
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = os.environ.get('MMX4_WORK', str(ROOT))
BUNDLED = os.environ.get('MMX4_BUNDLED', '')

HARAKAT = dict.fromkeys([0x064B, 0x064C, 0x064D, 0x064E, 0x064F, 0x0650,
                         0x0651, 0x0652, 0x0653, 0x0654, 0x0655, 0x0670])


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AR


ar = {}
data_dir = os.path.join(WORK, 'data')
for f in ('ar_batch1.py', 'ar_batch2.py', 'ar_fixes.py'):
    batch_file = os.path.join(data_dir, f)
    if os.path.exists(batch_file):
        ar.update(load(batch_file, f[:-3]))

# normalise: strip harakat (native font has no combining marks)
ar = {k: v.translate(HARAKAT) for k, v in ar.items()}

source_json = os.path.join(data_dir, 'source_text.json')
if os.path.exists(source_json):
    src = json.load(open(source_json, encoding='utf-8'))
    entries = []
    for e in src['entries']:
        eid = e['id']
        entries.append({
            'id': eid,
            'original': e['source'],
            'translation': ar.get(eid, ''),
            'source_sha256': e['source_sha256'],
        })
else:
    # Fallback when raw source text is excluded for distribution
    entries = []
    for eid, translation in sorted(ar.items()):
        entries.append({
            'id': eid,
            'original': '',
            'translation': translation,
            'source_sha256': '',
        })

catalog = {
    'schema': 1,
    'language': 'ar',
    'entries': entries,
    'description': ('Arabic dialogue translation. Original English and stable campaign/message '
                    'IDs remain visible. Requires Arabic glyph coverage in the native font atlas.'),
}

outdir = os.path.join(WORK, 'out')
pkgdir = os.path.join(outdir, 'mmx4.localization.ar', '1.0.0')
os.makedirs(os.path.join(pkgdir, 'catalog'), exist_ok=True)

catpath = os.path.join(pkgdir, 'catalog', 'ar.json')
with open(catpath, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
    f.write('\n')

raw = open(catpath, 'rb').read()
size = len(raw)
sha = hashlib.sha256(raw).hexdigest()

manifest = '''format_version = 9
id = "mmx4.localization.ar"
version = "1.0.0"
name = "Arabic Dialogue"
author = "community"
description = "Arabic translation of the campaign dialogue records. Requires Arabic glyph coverage in the native font atlas."
resolver = "declarative"
save_compatibility = "isolated"

[[target]]
game_id = "SLUS-00561"
disc_sha256 = "3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b"

[[feature]]
id = "translation"
name = "Arabic Dialogue"
description = "Arabic translation of X and Zero's dialogue using the native game font. Requires a fresh boot."
group = "Languages"
channel = "experimental"
default_enabled = false

[[option]]
feature = "translation"
id = "language"
label = "Arabic"
type = "choice"
default = "ar"

[[option.choice]]
value = "ar"
label = "العربية"

[[resource]]
feature = "translation"
id = "catalog"
label = "Arabic translation catalog"
description = "Plain UTF-8 JSON with stable message IDs, original text and translated text."
file_patterns = "*.json"
file_description = "Translation JSON catalog"
format = "file"
hidden = true
default = "catalog/ar.json"
required = true
size = %d
sha256 = "%s"

[[plugin]]
feature = "translation"
id = "mmx4.translation"
order = 100
''' % (size, sha)

mpath = os.path.join(pkgdir, 'manifest.toml')
with open(mpath, 'w', encoding='utf-8', newline='\n') as f:
    f.write(manifest)

with open(os.path.join(outdir, 'ar_catalog.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('catalog entries:', len(entries))
print('translated      :', sum(1 for e in entries if e['translation'].strip()))
print('catalog bytes   :', size)
print('catalog sha256  :', sha)
print('package         :', pkgdir)
print()
print('sample:')
for e in entries[:2] + entries[10:11]:
    print(' ', e['id'])
    print('   EN:', repr(e['original'][:90]))
    print('   AR:', repr(e['translation'][:90]))
