#!/usr/bin/env python3
"""After saving CherrygroveCity in Porymap (Cmd+S), confirm the editor round-trip.

Compares Porymap's saved files with the committed build output, checks that the
map blocks and events are semantically identical, rebuilds the ROM and compares
its hash with the pre-save hash.

    python3 tools/gba/maps/claude_cherrygrove/porymap/roundtrip_check.py tools/vendor/gba/claude-cherrygrove <pre-save-sha256>
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path

game = Path(sys.argv[1]).resolve(); before = sys.argv[2] if len(sys.argv) > 2 else None
changed = subprocess.check_output(['git', '-C', str(game), 'status', '--short'], text=True).strip().splitlines()
print('files Porymap touched:', [l.split()[-1] for l in changed] or 'none')
for rel in ['data/maps/CherrygroveCity/map.json', 'data/layouts/layouts.json']:
    new = json.loads((game / rel).read_text()); old = json.loads(subprocess.check_output(['git', '-C', str(game), 'show', 'HEAD:' + rel]))
    print(rel, 'semantically identical' if new == old else 'DIFFERS')
for rel in ['data/layouts/CherrygroveCity/map.bin', 'data/layouts/CherrygroveCity/border.bin']:
    new = (game / rel).read_bytes(); old = subprocess.check_output(['git', '-C', str(game), 'show', 'HEAD:' + rel])
    print(rel, 'byte-identical' if new == old else 'DIFFERS')
root = Path(__file__).resolve().parents[4]
toolchain = next(p for p in (root / 'tools/vendor/gba').glob('arm-gnu-toolchain-14.2.rel1-*') if p.is_dir())
make = 'gmake' if subprocess.run(['which', 'gmake'], capture_output=True).returncode == 0 else 'make'
subprocess.run([make, '-C', str(game), '-j8', f'TOOLCHAIN={toolchain}'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
               env=dict(os.environ, PATH=str(toolchain / 'bin') + os.pathsep + os.environ['PATH']))
after = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
print('ROM after Porymap save:', after)
if before: print('matches pre-save ROM' if after == before else 'ROM DIFFERS from pre-save hash ' + before)
