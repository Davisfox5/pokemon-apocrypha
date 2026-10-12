#!/usr/bin/env python3
"""Package the rich Floccesy revision as an incremental patch over v2."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'tools/vendor/gba/johto-restart-game'
WORK = ROOT / 'tools/vendor/gba/floccesy-rich-work'
ART = ROOT / 'gba/art/floccesy-v3'
PATCH = ROOT / 'gba/floccesy-v3.patch'
roots = [
    'data/layouts/FloccesyTown',
    'data/maps/FloccesyTown',
    'data/tilesets/primary/floccesy',
    'data/tilesets/secondary/floccesy',
    'graphics/door_anims/floccesy',
    'src/field_door.c',
    'src/data/tilesets/headers.h',
]
parts = []
changed = []
for item in roots:
    source = BASE / item
    paths = [source] if source.is_file() else sorted(p for p in source.rglob('*') if p.is_file())
    for old in paths:
        rel = old.relative_to(BASE)
        new = WORK / rel
        if old.read_bytes() == new.read_bytes():
            continue
        result = subprocess.run(
            ['git', 'diff', '--no-index', '--binary', '--src-prefix=a/', '--dst-prefix=b/',
             '--', str(old.relative_to(ROOT)), str(new.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, check=False,
        )
        assert result.returncode == 1, (rel, result.stderr.decode())
        data = result.stdout
        data = data.replace(b'a/tools/vendor/gba/johto-restart-game/', b'a/')
        data = data.replace(b'b/tools/vendor/gba/floccesy-rich-work/', b'b/')
        parts.append(data)
        changed.append(str(rel))
PATCH.write_bytes(b''.join(parts))
subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=BASE, check=True)
subprocess.run(['git', 'apply', '--reverse', '--check', str(PATCH)], cwd=WORK, check=True)
report = {
    'base': 'installed Floccesy v2 in johto-restart-game',
    'incremental_patch': True,
    'changed_files': changed,
    'bytes': PATCH.stat().st_size,
    'sha256': hashlib.sha256(PATCH.read_bytes()).hexdigest(),
    'forward_check': True,
    'reverse_check': True,
}
(ART / 'evidence/patch.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
