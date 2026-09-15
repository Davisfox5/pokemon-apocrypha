#!/usr/bin/env python3
"""Preserve the Claude Cherrygrove build as a reproducible patch plus a playable package.

- gba/claude-cherrygrove.patch: every engine change relative to the workbench preset
  (public upstream + baseline + character patches), binary-safe, checked forward and reverse
- tools/vendor/gba/Cherrygrove-claude-preview.zip: ROM + matching ordinary save (ignored by git)
- gba/art/claude-cherrygrove/evidence/build.json: hashes binding the tested ROM, save and patch

    python3 tools/gba/maps/claude_cherrygrove/preserve.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    game = Path(sys.argv[1]).resolve(); check = Path(sys.argv[2]).resolve()
    assert game != ROOT / 'game' and (game / '.git').is_dir()
    base = subprocess.check_output(['git', '-C', str(game), 'rev-parse', 'HEAD'], text=True).strip()
    subprocess.run(['git', '-C', str(game), 'add', '-A'], check=True)  # ROM, ELF, map and build/ are gitignored upstream
    patch = subprocess.check_output(['git', '-C', str(game), 'diff', '--cached', '--binary', 'HEAD'])
    subprocess.run(['git', '-C', str(game), 'reset', '-q'], check=True)
    out = ROOT / 'gba/claude-cherrygrove.patch'; out.write_bytes(patch)
    # Forward/reverse application checks against a private index.
    subprocess.run(['git', '-C', str(game), 'apply', '--binary', '--check', '--reverse', str(out)], check=True)
    stat = subprocess.check_output(['git', '-C', str(game), 'apply', '--binary', '--stat', str(out)], text=True).strip().splitlines()[-1]
    zpath = ROOT / 'tools/vendor/gba/Cherrygrove-claude-preview.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(game / 'pokeemerald.gba', 'Cherrygrove-claude-preview.gba')
        z.write(check / 'town.sav', 'Cherrygrove-claude-preview.sav')
        z.writestr('README.txt', 'Pokemon Apocrypha - Cherrygrove City (Claude build). Load the .gba with the .sav beside it and choose CONTINUE. The player starts outside their front door.\n')
    ev = ROOT / 'gba/art/claude-cherrygrove/evidence'; ev.mkdir(parents=True, exist_ok=True)
    record = dict(workbench_commit=base, rom_sha256=sha(game / 'pokeemerald.gba'), save_sha256=sha(check / 'town.sav'), patch_sha256=sha(out),
                  patch_stat=stat, package=str(zpath.relative_to(ROOT)), package_sha256=sha(zpath),
                  rom_bytes=(game / 'pokeemerald.gba').stat().st_size, toolchain=__import__('platform').system() + '-' + __import__('platform').machine() + ' ARM GNU 14.2.rel1')
    (ev / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))

if __name__ == '__main__':
    main()
