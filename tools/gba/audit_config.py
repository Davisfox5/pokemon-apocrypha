#!/usr/bin/env python3
"""Verify the partial mechanics profile and inventory config declarations as JSON.

This is a source inventory, not a C preprocessor or runtime behavior test.
Conditional declarations are retained individually; comments are upstream evidence,
not independently verified claims about the retail games.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
manifest = json.loads((ROOT / 'gba/mechanics-profile.json').read_text())
head = subprocess.check_output(['git', '-C', str(ROOT / 'game'), 'rev-parse', 'HEAD'], text=True).strip()
if head != manifest['upstream_commit']:
    raise SystemExit('Unexpected engine revision; repeat the audit for the new pin.')
files = []
for path in sorted((ROOT / 'game/include/config').glob('*.h')):
    # The family roster is qualified separately; avoid a duplicate species ledger.
    if path.name == 'species_enabled.h':
        continue
    relative = str(path.relative_to(ROOT / 'game'))
    upstream = subprocess.check_output(['git', '-C', str(ROOT / 'game'), 'show', f'HEAD:{relative}'], text=True)
    definitions = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = re.match(r'^#define\s+(\w+)\s+(.+)', line)
        if match:
            value, _, comment = match[2].partition('//')
            definitions.append({'line': number, 'name': match[1], 'declared_value': value.strip(), 'upstream_comment': comment.strip()})
    files.append({'file': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'upstream_sha256': hashlib.sha256(upstream.encode()).hexdigest(), 'definitions': definitions})
checks = []
for entry in manifest['settings']:
    rows = next(f['definitions'] for f in files if f['file'] == entry['file'])
    values = [r['declared_value'] for r in rows if r['name'] == entry['setting']]
    if values != [entry['value']]:
        raise SystemExit(f"Profile drift: {entry['setting']}: {values}")
    checks.append(entry['setting'])
print(json.dumps({'upstream_commit': head, 'method': __doc__.strip(),
                  'profile_sha256': hashlib.sha256((ROOT / 'gba/mechanics-profile.patch').read_bytes()).hexdigest(),
                  'verified_profile_settings': checks, 'files': files}, indent=2))
