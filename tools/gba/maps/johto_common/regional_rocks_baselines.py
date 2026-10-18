"""Materialize read-only, exact revision inputs; never reset an engine checkout."""
from pathlib import Path
import argparse
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
p = argparse.ArgumentParser()
p.add_argument('engine', type=Path, help='Engine clone containing the documented source branches')
a = p.parse_args()
configs = json.loads((ROOT / 'gba/art/johto-common/rocks/regional-rollout/source/inputs.json').read_text())
for c in configs:
    revision = c['baseline_commit']
    for name in c['baseline_files']:
        data = subprocess.check_output(['git', '-C', str(a.engine), 'show', revision + ':' + name])
        dest = Path(c['baseline']) / name
        if dest.exists():
            assert dest.read_bytes().replace(b'\r\n', b'\n') == data.replace(b'\r\n', b'\n'), dest
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    print(c['map'], revision)
